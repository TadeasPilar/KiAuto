# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnologïa Industrial
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
# Adapted from: https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
"""
Log module

Handles logging initialization and formating.
"""
import sys
import logging

# Default domain, base name for the tool
domain = 'kiauto'
verbose_level = 2
do_separate = False


def get_logger(name=None):
    """Get a module for a submodule or the root logger if no name is provided"""
    return logging.getLogger(domain+'.'+name) if name else logging.getLogger(domain)


def set_domain(name):
    """Set the base name for the tool"""
    global domain
    domain = name


def set_level(logger, level):
    global verbose_level
    verbose_level = level
    if level >= 2:
        log_level = logging.DEBUG
    elif level == 1:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING
    logger.setLevel(log_level)


def get_level():
    return verbose_level


class FilterOnlyInfo(object):
    def filter(self, record):
        return record.levelno == logging.INFO


class FilterNoInfo(object):
    def filter(self, record):
        return record.levelno != logging.INFO


def init(separate_info=False):
    """Initialize the logging feature using a custom format and the specified verbosity level"""
    global do_separate
    do_separate = separate_info
    logger = get_logger()
    if not separate_info:
        ch = logging.StreamHandler()
        ch.setFormatter(CustomFormatter())
        logger.addHandler(ch)
    else:
        # Handler for all but info.
        # Outputs to stderr
        ch = logging.StreamHandler()
        ch.addFilter(FilterNoInfo())
        ch.setFormatter(CustomFormatter(sys.stderr))
        logger.addHandler(ch)
        # Handler for info.
        # Outputs to stdout
        ch = logging.StreamHandler(sys.stdout)
        ch.addFilter(FilterOnlyInfo())
        ch.setFormatter(CustomFormatter(sys.stdout, no_prefix=True))
        logger.addHandler(ch)
    return logger


class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors"""

    def __init__(self, stream=None, no_prefix=False):
        super(logging.Formatter, self).__init__()
        if sys.stderr.isatty():
            grey = "\x1b[38;21m"
            yellow = "\x1b[93;1m"
            red = "\x1b[91;1m"
            bold_red = "\x1b[91;21m"
            cyan = "\x1b[36;1m"
            reset = "\x1b[0m"
        else:
            grey = ""
            yellow = ""
            red = ""
            bold_red = ""
            cyan = ""
            reset = ""
        # format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
        format = "%(levelname)s:%(message)s (%(name)s - %(filename)s:%(lineno)d)"
        format_simple = "%(message)s" if no_prefix else "%(levelname)s:%(message)s"

        self.FORMATS = {
            logging.DEBUG: cyan + format + reset,
            logging.INFO: grey + format_simple + reset,
            logging.WARNING: yellow + format + reset,
            logging.ERROR: red + format + reset,
            logging.CRITICAL: bold_red + format + reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def flush_info():
    if verbose_level < 1:
        return
    f = sys.stdout if do_separate else sys.stderr
    f.write("\n")
    f.flush()


def info_progress(msg):
    if verbose_level < 1:
        return
    f = sys.stdout if do_separate else sys.stderr
    f.write('\r'+msg)
    f.flush()
