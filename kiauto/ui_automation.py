#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnologïa Industrial
# Copyright (c) 2019 Jesse Vincent (@obra)
# Copyright (c) 2018-2019 Seppe Stas (@seppestas) (Productize SPRL)
# Copyright (c) 2015-2016 Scott Bezek (@scottbez1)
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
# Adapted from: https://github.com/obra/kicad-automation-scripts
"""
Utility functions for UI automation with xdotool in a virtual framebuffer
with XVFB. Also includes utilities for accessing the clipboard for easily
and efficiently copy-pasting strings in the UI.

Based on splitflap/electronics/scripts/export_util.py by Scott Bezek
"""
import argparse
from contextlib import contextmanager
import os
import re
import shutil
import signal
from subprocess import Popen, CalledProcessError, TimeoutExpired, call, check_output, STDOUT, DEVNULL, run, PIPE
import sys
from tempfile import mkdtemp
import time
# python3-xvfbwrapper
from xvfbwrapper import Xvfb
from kiauto.file_util import get_log_files
from kiauto.misc import KICAD_VERSION_5_99, MISSING_TOOL, KICAD_DIED, __version__
import kiauto.misc

from kiauto import log
logger = log.get_logger(__name__)
time_out_scale = 1.0
img_tmp_dir = None


def set_time_out_scale(scale):
    global time_out_scale
    time_out_scale = scale


class PopenContext(Popen):

    def __exit__(self, type, value, traceback):
        logger.debug("Closing pipe with %d", self.pid)
        # Note: currently we don't communicate with the child so these cases are never used.
        # I keep them in case they are needed, but excluded from the coverage.
        # Also note that closing stdin needs extra handling, implemented in the parent class
        # but not here.
        # This can generate a deadlock
        # if self.stdout:
        #     self.stdout.close()  # pragma: no cover
        if self.stderr:
            self.stderr.close()  # pragma: no cover
        if self.stdin:
            self.stdin.close()   # pragma: no cover
        if type:
            logger.debug("Terminating %d", self.pid)
            # KiCad nightly uses a shell script as intermediate to run setup the environment
            # and run the proper binary. If we simply call "terminate" we just kill the
            # shell script. So we create a group and then kill the whole group.
            try:
                os.killpg(os.getpgid(self.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            # self.terminate()
        # Wait for the process to terminate, to avoid zombies.
        try:
            # Wait for 3 seconds
            self.wait(3)
            retry = False
        except TimeoutExpired:  # pragma: no cover
            # The process still alive after 3 seconds
            retry = True
            pass
        if retry:  # pragma: no cover
            logger.debug("Killing %d", self.pid)
            # We shouldn't get here. Kill the process and wait upto 10 seconds
            os.killpg(os.getpgid(self.pid), signal.SIGKILL)
            # self.kill()
            self.wait(10)


def wait_xserver(out_dir, num_try):
    global time_out_scale
    timeout = 10*time_out_scale
    DELAY = 0.5
    logger.debug('Waiting for virtual X server ...')
    try:
        logger.debug('Current DISPLAY is '+os.environ['DISPLAY'])
    except KeyError:
        logger.error('Missing DISPLAY on wait_xserver!')
    if shutil.which('setxkbmap'):
        cmd = ['setxkbmap', '-query']
    elif shutil.which('xset'):  # pragma: no cover
        cmd = ['xset', 'q']
    else:  # pragma: no cover
        cmd = ['ls']
        logger.warning('No setxkbmap nor xset available, unable to verify if X is running')
    for i in range(int(timeout/DELAY)):
        logger.debug('Checking using '+str(cmd))
        flog_out, flog_err, _ = get_log_files(out_dir, cmd[0])
        ret = call(cmd, stdout=flog_out, stderr=flog_err, close_fds=True)
        if not ret:
            time_wait = 0.5*(num_try+1)*(num_try+1)*time_out_scale
            if log.get_level() > 2:
                logger.debug(str(cmd)+' returned 0')
                logger.debug('Waiting {} seconds before using the X server'.format(time_wait))
            # On GitLab I saw setxkbmap success and recordmydesktop and KiCad failing to connect to X
            # One possible solution is a wait here.
            # Another is detecting KiCad exited.
            time.sleep(time_wait)
            return
        logger.debug('   Retry')
        time.sleep(DELAY)
    raise RuntimeError('Timed out waiting for virtual X server')


def wait_wm():
    global time_out_scale
    timeout = 10*time_out_scale
    DELAY = 0.5
    logger.debug('Waiting for Window Manager ...')
    if shutil.which('wmctrl'):
        cmd = ['wmctrl', '-m']
    else:  # pragma: no cover
        logger.warning('No wmctrl, unable to verify if WM is running')
        time.sleep(2)
        return
    logger.debug('Checking using '+str(cmd))
    for i in range(int(timeout/DELAY)):
        ret = call(cmd, stdout=DEVNULL, stderr=STDOUT, close_fds=True)
        if not ret:
            return
        logger.debug('   Retry')
        time.sleep(DELAY)
    raise RuntimeError('Timed out waiting for WM server')


@contextmanager
def start_wm(do_it):
    if do_it:
        cmd = ['fluxbox']
        logger.debug('Starting WM: '+str(cmd))
        with PopenContext(cmd, stdout=DEVNULL, stderr=DEVNULL, close_fds=True, start_new_session=True) as wm_proc:
            wait_wm()
            try:
                yield
            finally:
                logger.debug('Terminating the WM')
                # Fluxbox sometimes will ignore SIGTERM, we can just kill it
                wm_proc.kill()
    else:
        yield


@contextmanager
def start_record(do_record, video_dir, video_name):
    if do_record:
        video_filename = os.path.join(video_dir, video_name)
        cmd = ['recordmydesktop', '--overwrite', '--no-sound', '--no-frame', '--on-the-fly-encoding',
               '-o', video_filename]
        logger.debug('Recording session with: '+str(cmd))
        flog_out, flog_err, _ = get_log_files(video_dir, cmd[0])
        with PopenContext(cmd, stdout=flog_out, stderr=flog_err, close_fds=True, start_new_session=True) as screencast_proc:
            try:
                yield
            finally:
                logger.debug('Terminating the session recorder')
                screencast_proc.terminate()
    else:
        yield


@contextmanager
def start_x11vnc(do_it, old_display):
    if do_it:
        if not shutil.which('x11vnc'):
            logger.error("x11vnc isn't installed, please install it")
            yield
        else:
            cmd = ['x11vnc', '-display', os.environ['DISPLAY'], '-localhost']
            logger.debug('Starting VNC server: '+str(cmd))
            with PopenContext(cmd, stdout=DEVNULL, stderr=DEVNULL, close_fds=True, start_new_session=True) as x11vnc_proc:
                if old_display is None:
                    old_display = ':0'
                logger.debug('To monitor the Xvfb now you can start: "ssvncviewer '+old_display+'"(or similar)')
                try:
                    yield
                finally:
                    logger.debug('Terminating the x11vnc server')
                    x11vnc_proc.terminate()
    else:
        yield


@contextmanager
def recorded_xvfb(cfg, num_try=0):
    old_display = os.environ.get('DISPLAY')
    if cfg.record and shutil.which('recordmydesktop') is None:
        logger.error('To record the session please install `recordmydesktop`')
        cfg.record = False
    with Xvfb(width=cfg.rec_width, height=cfg.rec_height, colordepth=cfg.colordepth):
        wait_xserver(cfg.output_dir, num_try)
        with start_x11vnc(cfg.start_x11vnc, old_display):
            with start_wm(cfg.use_wm):
                with start_record(cfg.record, cfg.video_dir, cfg.video_name):
                    yield


def xdotool(command, id=None):
    if id is not None:
        command.insert(1, str(id))
        command.insert(1, '--window')
    logger.debug(['xdotool'] + command)
    return check_output(['xdotool'] + command, stderr=DEVNULL).decode()
    # return check_output(['xdotool'] + command)


# def clipboard_store(string):
#     # I don't know how to use Popen/run to make it run with pipes without
#     # either blocking or losing the messages.
#     # Using files works really well.
#     logger.debug('Clipboard store "'+string+'"')
#     # Write the text to a file
#     fd_in, temp_in = tempfile.mkstemp(text=True)
#     os.write(fd_in, string.encode())
#     os.close(fd_in)
#     # Capture output
#     fd_out, temp_out = tempfile.mkstemp(text=True)
#     process = Popen(['xclip', '-selection', 'clipboard', temp_in], stdout=fd_out, stderr=STDOUT)
#     ret_code = process.wait()
#     os.remove(temp_in)
#     os.lseek(fd_out, 0, os.SEEK_SET)
#     ret_text = os.read(fd_out, 1000)
#     os.close(fd_out)
#     os.remove(temp_out)
#     ret_text = ret_text.decode()
#     if ret_text:  # pragma: no cover
#         logger.error('Failed to store string in clipboard')
#         logger.error(ret_text)
#         raise
#     if ret_code:  # pragma: no cover
#         logger.error('Failed to store string in clipboard')
#         logger.error('xclip returned %d' % ret_code)
#         raise


def text_replace(string):
    """ Used to replace a text in an input text widget. """
    delay = str(int(12*time_out_scale))
    cmd = ['key', '--delay', delay, 'ctrl+a', 'type', '--delay', delay, string]
    logger.debug('text_replace with: {}'.format(cmd))
    xdotool(cmd)


def clipboard_retrieve():
    p = Popen(['xclip', '-o', '-selection', 'clipboard'], stdout=PIPE, stderr=STDOUT)
    output = ''
    for line in p.stdout:
        output += line.decode()
    logger.debug('Clipboard retrieve "'+output+'"')
    return output


def get_windows(all=False):
    cmd = ['search', '--name', '.*']
    if not all:
        cmd.insert(1, '--onlyvisible')
    ids = xdotool(cmd).splitlines()
    res = []
    for i in ids:
        name = ''
        try:
            name = xdotool(['getwindowname', i])[:-1]
        except CalledProcessError:
            name = '** No longer there **'
        res.append((i, name))
        if log.get_level() >= 2:
            logger.debug('get_windows {} {}'.format(i, name))
    if log.get_level() >= 2:
        logger.debug('get_windows end of list')
    return res


def debug_window(id=None):  # pragma: no cover
    if log.get_level() < 2:
        return
    if shutil.which('xprop'):
        if id is None:
            try:
                id = xdotool(['getwindowfocus']).rstrip()
            except CalledProcessError:
                logger.debug('xdotool getwindowfocus failed!')
                pass
        if id:
            call(['xprop', '-id', id])
    if shutil.which('vmstat'):
        call(['vmstat', '-s'])
    if shutil.which('uptime'):
        call(['uptime'])
    logger.debug("Visible windows:")
    for i in get_windows():
        logger.debug("Window ID: `{}` ; name: `{}`".format(i[0], i[1]))
    logger.debug("All windows:")
    for i in get_windows(all=True):
        logger.debug("Window ID: `{}` ; name: `{}`".format(i[0], i[1]))


def wait_focused(id, timeout=10):
    global time_out_scale
    timeout *= time_out_scale
    DELAY = 0.5
    logger.debug('Waiting for %s window to get focus...', id)
    for i in range(min(int(timeout/DELAY), 1)):
        cur_id = xdotool(['getwindowfocus']).rstrip()
        logger.debug('Currently focused id: %s', cur_id)
        if cur_id == id:
            return
        time.sleep(DELAY)
    debug_window(cur_id)  # pragma: no cover
    raise RuntimeError('Timed out waiting for %s window to get focus' % id)


def wait_not_focused(id, timeout=10):
    global time_out_scale
    timeout *= time_out_scale
    DELAY = 0.5
    logger.debug('Waiting for %s window to lose focus...', id)
    for i in range(int(timeout/DELAY)):
        try:
            cur_id = xdotool(['getwindowfocus']).rstrip()
        except CalledProcessError:
            # When no window is available xdotool receives ID=1 and exits with error
            return
        logger.debug('Currently focused id: %s', cur_id)
        if cur_id != id:
            return
        time.sleep(DELAY)
    debug_window(cur_id)  # pragma: no cover
    raise RuntimeError('Timed out waiting for %s window to lose focus' % id)


def search_visible_windows(regex, others=None):
    """ Workaround for problems in xdotool failing to match window names """
    r = re.compile(regex)
    others = [] if others is None else others
    others_rx = [re.compile(v) for v in others]
    found = []
    windows = get_windows()
    # First check if we have one of the "others"
    for c, rx in enumerate(others_rx):
        for i in windows:
            if rx.search(i[1]):
                # Yes, inform it
                # Note: The main window can be focused with a dialog over it.
                #       If we found one of these dialogs it means we have a problem, no matters if the main windows is focused
                raise ValueError(others[c])
    # Now check for the window we need
    for i in windows:
        if r.search(i[1]):
            found.append(i[0])
    return found


def wait_for_window(name, window_regex, timeout=10, focus=True, skip_id=0, others=None, popen_obj=None):
    global time_out_scale
    timeout *= time_out_scale
    DELAY = 0.5
    logger.info('Waiting for "%s" ...', name)
    if skip_id:
        logger.debug('Will skip %s', skip_id)

    for i in range(int(timeout/DELAY)):
        try:
            window_id = search_visible_windows(window_regex, others=others)
            if len(window_id):
                logger.debug('Found %s window (%d)', name, len(window_id))
                if len(window_id) == 1:
                    id = window_id[0]
                if len(window_id) > 1:
                    id = window_id[1]
                logger.debug('Window id: %s', id)
                if id != skip_id:
                    if focus:
                        xdotool(['windowfocus', '--sync', id])
                        wait_focused(id, timeout)
                    return window_id
                else:
                    logger.debug('Skipped')
        except CalledProcessError:
            if popen_obj and popen_obj.poll() is not None:
                raise
        # Check if we have a list of alternative windows
        if others:
            for other in others:
                window_id = search_visible_windows(other)
                if len(window_id):
                    raise ValueError(other)
        if popen_obj:
            # Is KiCad running?
            ret_code = popen_obj.poll()
            if ret_code is not None:
                raise CalledProcessError(ret_code, 'KiCad')
        time.sleep(DELAY)
    debug_window()  # pragma: no cover
    raise RuntimeError('Timed out waiting for %s window' % name)


def wait_point(cfg):
    if cfg.wait_for_key:
        input('Press a key')


def capture_window_region(window_id, x, y, w, h, name):
    """ Capture a region of a window to a file """
    geometry = '{}x{}+{}+{}'.format(w, h, x, y)
    logger.debug('Capturing region {} from window {}'.format(geometry, window_id))
    name = os.path.join(img_tmp_dir, name)
    if not shutil.which('import'):
        logger.error("import isn't installed, please install it.\nThis is part of ImageMagick and GraphicsMagic packages.")
        sys.exit(MISSING_TOOL)
    res = check_output(['import', '-window', str(window_id), '-crop', geometry, name], stderr=DEVNULL).decode()
    logger.debug('Import output: ' + res)


def wait_window_get_ref(window_id, x, y, w, h):
    """ Takes a region of a window as reference image """
    global img_tmp_dir
    img_tmp_dir = mkdtemp(prefix='tmp-kiauto-images-')
    capture_window_region(window_id, x, y, w, h, "wait_ref.png")


def wait_window_change(window_id, x, y, w, h, time_out):
    """ Waits for a change in a window region """
    for i in range(int(time_out + 0.9)):
        capture_window_region(window_id, x, y, w, h, "current.png")
        current = os.path.join(img_tmp_dir, "current.png")
        wait_ref = os.path.join(img_tmp_dir, "wait_ref.png")
        difference = os.path.join(img_tmp_dir, "difference.png")
        res = run(['compare', '-fuzz', '5%', '-metric', 'AE', current, wait_ref, difference],
                  stderr=PIPE).stderr.decode()
        ae = int(res)
        logger.debug('Difference ' + res)
        if ae:
            shutil.rmtree(img_tmp_dir)
            return
        time.sleep(1)
    shutil.rmtree(img_tmp_dir)


def open_dialog_with_retry(msg, keys, desc, w_name, cfg, id_dest=None):
    logger.info(msg)
    wait_point(cfg)
    if cfg.kicad_version >= KICAD_VERSION_5_99:
        # KiCad 6 has a very slow start-up
        time.sleep(1)
    xdotool(keys, id=id_dest)
    retry = False
    try:
        id = wait_for_window(desc, w_name, popen_obj=cfg.popen_obj, others=['pcbnew Warning'])
    except RuntimeError:  # pragma: no cover
        # Perhaps the main window wasn't available yet
        retry = True
    except CalledProcessError as e:
        logger.error(str(e))
        sys.exit(KICAD_DIED)
    except ValueError:
        logger.warning('Got pcbnew warning dialog, trying to dismiss it')
        xdotool(['key', 'Return'])
        retry = True
    if retry:
        logger.info('"{}" did not open, retrying'.format(desc))
        # wait_eeschema_start(cfg)
        xdotool(keys, id=id_dest)
        try:
            id = wait_for_window(desc, w_name, popen_obj=cfg.popen_obj)
        except CalledProcessError as e:
            logger.error(str(e))
            sys.exit(KICAD_DIED)
    return id


def show_info():
    print("This is KiAuto v"+__version__)
    print("Installed at: "+os.path.abspath(sys.argv[0]))
    print("Using kiauto module from: "+os.path.dirname(kiauto.misc.__file__))
    print("Interpreted by Python: {} (v{})".format(sys.executable, sys.version.replace('\n', ' ')))
    print("Tools:")
    try:
        import pcbnew
        kicad_version = pcbnew.GetBuildVersion()
        print("- kicad: {} (v{})".format(shutil.which('kicad'), kicad_version))
    except ImportError:
        print("ERROR: Failed to import pcbnew Python module."
              " Is KiCad installed?"
              " Do you need to add it to PYTHONPATH?")
    print("- xdotool: "+str(shutil.which('xdotool')))
    print("- recordmydesktop: "+str(shutil.which('recordmydesktop')))
    print("- xsltproc: "+str(shutil.which('xsltproc')))
    print("- xclip: "+str(shutil.which('xclip')))
    print("- convert: "+str(shutil.which('convert')))


class ShowInfoAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        show_info()
        exit(0)
