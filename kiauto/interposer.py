# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnologïa Industrial
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
import atexit
import os
import platform
from queue import Queue, Empty
import shutil
from sys import exit
from tempfile import mkdtemp
from threading import Thread
import time
from kiauto.misc import KICAD_DIED


KICAD_EXIT_MSG = '>>exit<<'
INTERPOSER_OPS = 'interposer_options.txt'


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
