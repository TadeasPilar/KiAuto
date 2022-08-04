# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnologïa Industrial
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
import atexit
import os
import platform
from queue import Queue, Empty
import re
import shutil
from sys import exit
from tempfile import mkdtemp
from threading import Thread
import time
from kiauto.misc import KICAD_DIED, CORRUPTED_PCB, PCBNEW_ERROR, EESCHEMA_ERROR
from kiauto import log
from kiauto.ui_automation import xdotool, wait_for_window

KICAD_EXIT_MSG = '>>exit<<'
INTERPOSER_OPS = 'interposer_options.txt'
IGNORED_DIALOG_MSGS = {'The quick brown fox jumps over the lazy dog.', '0123456789'}


def check_interposer(args, logger, cfg):
    # Name of the interposer library
    interposer_lib = os.path.abspath(os.path.join(os.path.dirname(__file__), 'interposer', 'libinterposer.so'))
    if (not os.path.isfile(interposer_lib) or  # The lib isn't there
       args.disable_interposer or             # The user disabled it
       platform.system() != 'Linux' or 'x86_64' not in platform.platform()):  # Not Linux 64 bits x86
        interposer_lib = None
    else:
        os.environ['LD_PRELOAD'] = interposer_lib
        logger.debug('** Using interposer: '+interposer_lib)
    cfg.use_interposer = interposer_lib
    cfg.enable_interposer = interposer_lib or args.interposer_sniff
    cfg.logger = logger


last_msg_time = 0
interposer_dialog = []


def dump_interposer_dialog(cfg):
    cfg.logger.debug('Storing interposer dialog ({})'.format(cfg.flog_int.name))
    if cfg.enable_interposer and not cfg.use_interposer:
        try:
            global last_msg_time
            while True:
                tm, line = cfg.kicad_q.get(timeout=.1)
                tm *= 1000
                diff = 0
                if last_msg_time:
                    diff = tm-last_msg_time
                last_msg_time = tm
                interposer_dialog.append('>>Interposer<<:{} (@{} D {})'.format(line[:-1], round(tm, 3), round(diff, 3)))
        except Empty:
            pass
    for ln in interposer_dialog:
        cfg.flog_int.write(ln+'\n')
    cfg.flog_int.close()


def remove_interposer_print_dir(cfg):
    cfg.logger.debug('Removing temporal dir '+cfg.interposer_print_dir)
    shutil.rmdir(cfg.interposer_print_dir)


def create_interposer_print_options_file(cfg):
    # We need a file to save the print options, make it unique to avoid collisions
    cfg.interposer_print_dir = mkdtemp()
    cfg.interposer_print_file = os.path.join(cfg.interposer_print_dir, INTERPOSER_OPS)
    cfg.logger.debug('Using temporal file {} for interposer print options'.format(cfg.interposer_print_file))
    os.environ['KIAUTO_INTERPOSER_PRINT'] = cfg.interposer_print_file
    atexit.register(remove_interposer_print_dir, cfg)


# def flush_queue():
#     """ Thread safe queue flush """
#     with cfg.kicad_q.mutex:
#         cfg.kicad_q.queue.clear()


def enqueue_output(out, queue):
    """ Read 1 line from the interposer and add it to the queue.
        Notes:
        * The queue is thread safe.
        * When we get an empty string we finish, this is the case for KiCad finished """
    tm_start = time.time()
    for line in iter(out.readline, ''):
        queue.put((time.time()-tm_start, line))
        # logger.error((time.time()-tm_start, line))
    out.close()


# https://stackoverflow.com/questions/375427/a-non-blocking-read-on-a-subprocess-pipe-in-python
def start_queue(cfg):
    """ Create a communication queue in a separated thread.
        It will collect all messages from the interposer. """
    if not cfg.enable_interposer:
        return
    cfg.logger.debug('Starting queue thread')
    cfg.kicad_q = Queue()
    # Avoid crashes when KiCad 5 sends an invalid Unicode sequence
    cfg.popen_obj.stdout.reconfigure(errors='ignore')
    cfg.kicad_t = Thread(target=enqueue_output, args=(cfg.popen_obj.stdout, cfg.kicad_q))
    cfg.kicad_t.daemon = True   # thread dies with the program
    cfg.kicad_t.start()


def wait_queue(cfg, strs='', starts=False, times=1, timeout=300, do_to=True, kicad_can_exit=False):
    """ Wait for a string in the queue """
    if not cfg.use_interposer:
        return None
    if isinstance(strs, str):
        strs = [strs]
    end_time = time.time()+timeout*cfg.time_out_scale
    msg = 'Waiting for `{}` starts={} times={}'.format(strs, starts, times)
    interposer_dialog.append('KiAuto:'+msg)
    if cfg.verbose > 1:
        cfg.logger.debug(msg)
    global last_msg_time
    while time.time() < end_time:
        try:
            tm, line = cfg.kicad_q.get(timeout=.1)
            if cfg.verbose > 1:
                tm *= 1000
                diff = 0
                if last_msg_time:
                    diff = tm-last_msg_time
                last_msg_time = tm
                cfg.logger.debug('>>Interposer<<:{} (@{} D {})'.format(line[:-1], round(tm, 3), round(diff, 3)))
            interposer_dialog.append(line[:-1])
        except Empty:
            line = ''
        if line == '' and cfg.popen_obj.poll() is not None:
            if kicad_can_exit:
                return KICAD_EXIT_MSG
            cfg.logger.error('KiCad unexpectedly died (error level {})'.format(cfg.popen_obj.poll()))
            exit(KICAD_DIED)
        old_times = times
        for s in strs:
            if s == '':
                # Waiting for anything ... but not for nothing
                if line != '':
                    return line[:-1]
                continue
            if starts:
                if line.startswith(s):
                    times -= 1
                    break
            elif line[:-1] == s:
                times -= 1
                break
        if times == 0:
            interposer_dialog.append('KiAuto:match')
            return line[:-1]
        if old_times != times:
            interposer_dialog.append('KiAuto:times '+str(times))
    if do_to:
        raise RuntimeError('Timed out waiting for `{}`'.format(strs))


def collect_dialog_messages(cfg, title):
    cfg.logger.info(title+' dialog found ...')
    cfg.logger.debug('Gathering potential dialog content')
    msgs = set()
    for msg in range(12):
        res = wait_queue(cfg, timeout=0.1, do_to=False)
        if res is None:
            # Some dialogs has less messages
            continue
        if res.startswith('PANGO:'):
            res = res[6:]
            if res not in IGNORED_DIALOG_MSGS:
                msgs.add(res)
    cfg.logger.debug('Messages: '+str(msgs))
    return msgs


def unknown_dialog(cfg, title, msgs=None):
    if msgs is None:
        msgs = collect_dialog_messages(cfg, title)
    cfg.logger.error('Unknown KiCad dialog: '+title)
    cfg.logger.error('Potential dialog messages: '+str(msgs))
    exit(PCBNEW_ERROR if cfg.is_pcbnew else EESCHEMA_ERROR)


def dismiss_dialog(cfg, title, keys):
    cfg.logger.debug('Dismissing dialog `{}` using {}'.format(title, keys))
    wait_for_window(title, title, 1)
    if isinstance(keys, str):
        keys = [keys]
    xdotool(['key']+keys)


def dismiss_error(cfg, title):
    """ KiCad 6: Corrupted PCB/Schematic
        KiCad 5: Newer KiCad needed  for PCB, missing sch lib """
    msgs = collect_dialog_messages(cfg, title)
    if "Error loading PCB '"+cfg.input_file+"'." in msgs:
        # KiCad 6 PCB loading error
        cfg.logger.error('Error loading PCB file. Corrupted?')
        exit(CORRUPTED_PCB)
    if "Error loading schematic '"+cfg.input_file+"'." in msgs:
        # KiCad 6 schematic loading error
        cfg.logger.error('Error loading schematic file. Corrupted?')
        exit(EESCHEMA_ERROR)
    if 'KiCad was unable to open this file, as it was created with' in msgs:
        # KiCad 5 PCBnew loading a KiCad 6 file
        cfg.logger.error('Error loading PCB file. Needs KiCad 6?')
        exit(CORRUPTED_PCB)
    if 'Use the Manage Symbol Libraries dialog to fix the path (or remove the library).' in msgs:
        # KiCad 5 Eeschema missing lib. Should be a warning, not an error dialog
        cfg.logger.warning('Missing libraries, please fix it')
        dismiss_dialog(cfg, title, 'Return')
        return
    unknown_dialog(cfg, title, msgs)


def dismiss_file_open_error(cfg, title):
    """ KiCad 6: File is already opened """
    msgs = collect_dialog_messages(cfg, title)
    kind = 'PCB' if cfg.is_pcbnew else 'Schematic'
    fname = os.path.basename(cfg.input_file)
    if 'Open Anyway' in msgs and kind+" '"+fname+"' is already open." in msgs:
        cfg.logger.warning('This file is already opened ({})'.format(fname))
        dismiss_dialog(cfg, title, ['Left', 'Return'])
        return
    unknown_dialog(cfg, title, msgs)


def dismiss_already_running(cfg, title):
    """ KiCad 5: Program already running """
    msgs = collect_dialog_messages(cfg, title)
    kind = 'pcbnew' if cfg.is_pcbnew else 'eeschema'
    if kind+' is already running. Continue?' in msgs:
        cfg.logger.warning(kind+' is already running')
        dismiss_dialog(cfg, title, 'Return')
        return
    unknown_dialog(cfg, title, msgs)


def dismiss_already_open(cfg, title):
    """ KiCad 5 when already open file """
    msgs = collect_dialog_messages(cfg, title)
    kind = 'PCB' if cfg.is_pcbnew else 'Schematic'
    if kind+' file "'+cfg.input_file+'" is already open.' in msgs:
        cfg.logger.error('File already opened by another KiCad instance')
        exit(PCBNEW_ERROR if cfg.is_pcbnew else EESCHEMA_ERROR)
    unknown_dialog(cfg, title, msgs)


def wait_start_by_msg(cfg):
    cfg.logger.info('Waiting for PCB new window ...')
    pre = 'GTK:Window Title:'
    pre_l = len(pre)
    cfg.logger.debug('Waiting pcbnew to start and load the PCB')
    # Inform the elapsed time for slow loads
    pres = [pre, 'PANGO:0:']
    elapsed_r = re.compile(r'PANGO:(\d:\d\d:\d\d)')
    if cfg.is_pcbnew:
        kind = 'PCB'
        prg_name = 'Pcbnew'
        unsaved = '  [Unsaved]'
    else:
        kind = 'Schematic'
        prg_name = 'Eeschema'
        unsaved = ' noname.sch'
    loading_msg = 'Loading '+kind
    prg_msg = prg_name+' —'
    kicad6_title = ' — '+kind+' Editor'
    with_elapsed = False
    while True:
        # Wait for any window
        res = wait_queue(cfg, pres, starts=True, timeout=cfg.wait_start)
        cfg.logger.debug('wait_pcbew_start_by_msg got '+res)
        match = elapsed_r.match(res)
        title = res[pre_l:]
        if not match and with_elapsed:
            log.flush_info()
        if not cfg.ki5 and title.endswith(kicad6_title):
            # KiCad 6
            if title.startswith('[no schematic loaded]'):
                # False alarma, nothing loaded
                continue
            # KiCad finished the load process
            if title[0] == '*':
                # This is an old format file that will be saved in the new format
                cfg.logger.warning('Old file format detected, please convert it to KiCad 6 if experimenting problems')
            return
        elif cfg.ki5 and title.startswith(prg_msg):
            # KiCad 5 title
            if not title.endswith(unsaved):
                # KiCad 5 name is "Pcbnew — PCB_NAME" or "Eeschema — SCH_NAME [HIERARCHY] — SCH_FILE_NAME"
                # wait_pcbnew()
                return
            # The "  [Unsaved]" is changed before the final load, ignore it
        elif title == '' or title == cfg.pn_simple_window_title or title == 'Eeschema':
            # This is the main window before loading anything
            # Note that KiCad 5 can create dialogs BEFORE this
            pass
        elif title == loading_msg:
            # This is the dialog for the loading progress, wait
            pass
        elif match is not None:
            log.info_progress('Elapsed time: '+match.group(1))
            with_elapsed = True
        elif title == 'Error':
            dismiss_error(cfg, title)
        elif title == 'File Open Error':
            dismiss_file_open_error(cfg, title)
        elif title == 'Confirmation':
            dismiss_already_running(cfg, title)
        elif title == 'Warning':
            dismiss_already_open(cfg, title)
        else:
            unknown_dialog(cfg, title)
