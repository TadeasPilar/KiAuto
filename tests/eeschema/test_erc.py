# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnologïa Industrial
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
"""
Tests for eeschema_do run_erc

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
import pytest
import logging
# Look for the 'utils' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
prev_dir = os.path.dirname(script_dir)
sys.path.insert(0, prev_dir)
# Utils import
from utils import context
sys.path.insert(0, os.path.dirname(prev_dir))
from kiauto.misc import (WRONG_ARGUMENTS, Config)

PROG = 'eeschema_do'
OUT_ERR_REX = r'(\d+) ERC errors'
OUT_WAR_REX = r'(\d+) ERC warnings'
OUT_IG_ERR_REX = r'Ignoring (\d+) ERC error/s'
OUT_IG_WAR_REX = r'Ignoring (\d+) ERC warning/s'


def test_erc_ok_1(test_dir):
    """ 1) Test a project with 0 ERC errors/warnings.
        2) Test the --record option.
        3) Test the case when the .erc report aready exists. """
    prj = 'good-project'
    erc = prj+'.erc'
    ctx = context.TestContextSCH(test_dir, 'ERC_Ok', prj)
    # Force removing the .erc
    ctx.create_dummy_out_file(erc)
    cmd = [PROG, '-vv', '--record', 'run_erc']
    ctx.run(cmd)
    ctx.expect_out_file(erc)
    ctx.expect_out_file('run_erc_eeschema_screencast.ogv')
    ctx.clean_up()


def test_erc_fail(test_dir):
    """ Test a project with 1 ERC error and 2 ERC warnings """
    prj = 'fail-project'
    ctx = context.TestContextSCH(test_dir, 'ERC_Error', prj)
    cmd = [PROG, 'run_erc']
    ctx.run(cmd, 255)
    ctx.expect_out_file(prj+'.erc')
    m = ctx.search_err(OUT_ERR_REX)
    assert m is not None
    assert m.group(1) == '1'
    m = ctx.search_err(OUT_WAR_REX)
    assert m is not None
    assert m.group(1) == '2'
    ctx.clean_up()


def test_erc_warning_1(test_dir):
    prj = 'warning-project'
    ctx = context.TestContextSCH(test_dir, 'test_erc_warning_1', prj)
    cmd = [PROG, 'run_erc']
    ctx.run(cmd, 0)
    ctx.expect_out_file(prj+'.erc')
    m = ctx.search_err(OUT_WAR_REX)
    assert m is not None
    assert m.group(1) == '1'
    ctx.clean_up()


def test_erc_warning_fail(test_dir):
    prj = 'warning-project'
    ctx = context.TestContextSCH(test_dir, 'test_erc_warning_fail', prj)
    cmd = [PROG, 'run_erc', '--warnings_as_errors']
    ctx.run(cmd, 255)
    ctx.expect_out_file(prj+'.erc')
    m = ctx.search_err(OUT_ERR_REX)
    assert m is not None
    assert m.group(1) == '1'
    ctx.clean_up()


def test_erc_ok_eeschema_running(test_dir):
    """ 1) Test eeschema already running
        2) Test logger colors on TTYs """
    prj = 'good-project'
    rep = prj+'.erc'
    ctx = context.TestContextSCH(test_dir, 'ERC_Ok_eeschema_running', prj)
    cfg = Config(logging)
    # Run eeschema in parallel to get 'Dismiss eeschema already running'
    with ctx.start_kicad(cfg.eeschema, cfg):
        # Enable DEBUG logs
        cmd = [PROG, '-vv', '-r', 'run_erc']
        # Use a TTY to get colors in the DEBUG logs
        ctx.run(cmd, use_a_tty=True)
        ctx.stop_kicad()
    ctx.expect_out_file(rep)
    logging.debug('Checking for colors in DEBUG logs')
    assert ctx.search_err(r"\[36;1mDEBUG:") is not None
    if context.ki5:
        # Only KiCad 5 reports it as a problem
        assert ctx.search_err(r"already running") is not None
    ctx.clean_up()


@pytest.mark.skipif(not context.ki5, reason="Test for KiCad 4 file under KiCad 5")
def test_erc_remap(test_dir):
    """ Here we use a KiCad 4 .sch that needs symbol remapping """
    prj = 'kicad4-project'
    rep = prj+'.erc'
    ctx = context.TestContextSCH(test_dir, 'ERC_Remap', prj, True)
    cmd = [PROG, '-vv', '-r', 'run_erc']
    # This is an old project that I can't edit.
    # KiCad 6 reports various issues.
    # This check is oriented to check we detect the need for update.
    # It doesn't work any more on KiCad 5.99 20210107.
    # It opens a new window, not really modal, the main window keeps the focus,
    # but doesn't respond until the other is finished.
    # KiCad is fully broken about handling modal dialogs, they blame wxWidgets,
    # but what they do is a really useless workaround.
    ctx.run(cmd, ignore_ret=True)
    ctx.expect_out_file(rep)
    assert ctx.search_err(r"Schematic needs update") is not None
    ctx.clean_up()


@pytest.mark.skipif(not context.ki5, reason="Test for KiCad 5 schematic libs")
def test_erc_error(test_dir):
    """ Here we have a missing library.
        On KiCad 6 there is no need for the libs. """
    prj = 'missing-lib'
    rep = prj+'.erc'
    ctx = context.TestContextSCH(test_dir, 'ERC_Error', prj)
    cmd = [PROG, 'run_erc']
    ctx.run(cmd)
    ctx.expect_out_file(rep)
    assert ctx.search_err(r"Missing librar") is not None
    ctx.clean_up()


def test_erc_filter_1(test_dir):
    """ Test a project with 1 ERC error and 2 ERC warnings.
        But we are filtering all of them. """
    prj = 'fail-project'
    ctx = context.TestContextSCH(test_dir, 'ERC_Filter', prj)
    cmd = [PROG, '-v', 'run_erc', '-f', ctx.get_prodir_filename('fail.filter')]
    ctx.run(cmd)
    ctx.expect_out_file(prj+'.erc')
    m = ctx.search_err(OUT_IG_ERR_REX)
    assert m is not None
    assert m.group(1) == '1'
    m = ctx.search_err(OUT_IG_WAR_REX)
    assert m is not None
    assert m.group(1) == '2'
    ctx.clean_up()


def test_erc_filter_bad_name(test_dir):
    """ Wrong filter name. """
    prj = 'fail-project'
    ctx = context.TestContextSCH(test_dir, 'ERC_Filter_Bad_Name', prj)
    cmd = [PROG, '-v', 'run_erc', '-f', ctx.get_prodir_filename('bogus')]
    ctx.run(cmd, WRONG_ARGUMENTS)
    m = ctx.search_err(r"Filter file (.*) doesn't exist")
    assert m is not None
    ctx.clean_up()


def test_erc_filter_bad_syntax(test_dir):
    """ Wrong filter name. """
    prj = 'fail-project'
    ctx = context.TestContextSCH(test_dir, 'ERC_Filter_Bad_Syntax', prj)
    cmd = [PROG, '-v', 'run_erc', '-f', ctx.get_prodir_filename('sym-lib-table')]
    ctx.run(cmd, WRONG_ARGUMENTS)
    m = ctx.search_err(r"Syntax error at line \d+ in filter file")
    assert m is not None
    ctx.clean_up()
