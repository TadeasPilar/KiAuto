# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnologïa Industrial
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
"""
Tests for 'pcbnew_do run_drc'

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
import logging
import shutil
# Look for the 'utils' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
prev_dir = os.path.dirname(script_dir)
sys.path.insert(0, prev_dir)
# Utils import
from utils import context
sys.path.insert(0, os.path.dirname(prev_dir))
from kiauto.misc import Config

PROG = 'pcbnew_do'
REPORT = 'drc_result.rpt'
OUT_REX = r'(\d+) DRC errors and (\d+) unconnected pads'
DEFAULT = 'printed.pdf'


def test_drc_ok_1(test_dir):
    """ Also test logger colors on TTYs """
    ctx = context.TestContext(test_dir, 'DRC_Ok', 'good-project')
    cmd = [PROG, '-vv', 'run_drc']
    ctx.run(cmd)
    ctx.expect_out_file(REPORT)
    ctx.clean_up()


def test_drc_fail(test_dir):
    ctx = context.TestContext(test_dir, 'DRC_Error', 'fail-project')
    # Here we use -v to cover "info" log level
    cmd = [PROG, '-v', 'run_drc']
    ctx.run(cmd, 254)
    ctx.expect_out_file(REPORT)
    m = ctx.search_err(OUT_REX)
    assert m is not None
    assert m.group(1) == '1'
    assert m.group(2) == '1'
    ctx.clean_up()


def test_drc_unco(test_dir):
    ctx = context.TestContext(test_dir, 'DRC_Unconnected', 'warning-project')
    cmd = [PROG, 'run_drc', '--output_name', 'drc.txt']
    ctx.run(cmd, 255)
    ctx.expect_out_file('drc.txt')
    m = ctx.search_err(OUT_REX)
    assert m is not None
    assert m.group(1) == '0'
    assert m.group(2) == '1'
    ctx.clean_up()


def test_drc_unco_ok(test_dir):
    ctx = context.TestContext(test_dir, 'DRC_Unconnected_Ok', 'warning-project')
    cmd = [PROG, 'run_drc', '--output_name', 'drc.txt', '--ignore_unconnected']
    ctx.run(cmd)
    ctx.expect_out_file('drc.txt')
    m = ctx.search_err(OUT_REX)
    assert m is not None
    assert m.group(1) == '0'
    assert m.group(2) == '1'
    ctx.clean_up()


def test_drc_ok_pcbnew_running(test_dir):
    """ 1) Test to overwrite the .erc file
        2) Test pcbnew already running
        On KiCad 6 we don't run pcbnew """
    ctx = context.TestContext(test_dir, 'DRC_Ok_pcbnew_running', 'good-project')
    # Create a report to force and overwrite
    with open(ctx.get_out_path(REPORT), 'w') as f:
        f.write('dummy')
    cfg = Config(logging)
    # Run pcbnew in parallel to get 'Dismiss pcbnew already running'
    with ctx.start_kicad(cfg.pcbnew, cfg):
        # Enable DEBUG logs
        cmd = [PROG, '-vv', 'run_drc']
        # Use a TTY to get colors in the DEBUG logs
        ctx.run(cmd, use_a_tty=True)
        ctx.stop_kicad()
    ctx.expect_out_file(REPORT)
    logging.debug('Checking for colors in DEBUG logs')
    if ctx.kicad_version < context.KICAD_VERSION_5_99:
        assert ctx.search_err(r"is already running") is not None
    assert ctx.search_err(r"\[36;1mDEBUG:") is not None
    ctx.clean_up()


def test_drc_save(test_dir):
    """ Here we test a PCB with outdated zone fills.
        We run the DRC refilling, save it and then print. """
    ctx = context.TestContext(test_dir, 'DRC_Save_1', 'zone-refill')
    shutil.copy2(ctx.board_file+'.ok', ctx.board_file)
    cmd = [PROG, 'run_drc', '-s']
    ctx.run(cmd)
    ctx.expect_out_file(REPORT)
    ctx.clean_up()

    ctx = context.TestContext(test_dir, 'DRC_Save_2', 'zone-refill')
    cmd = [PROG, 'export']
    layers = ['F.Cu', 'B.Cu', 'Edge.Cuts']
    ctx.run(cmd, extra=layers)
    ctx.expect_out_file(DEFAULT)
    ctx.compare_image(DEFAULT, 'zone-refill.pdf')
    shutil.copy2(ctx.board_file+'.ok', ctx.board_file)
    ctx.clean_up()


def test_drc_no_save(test_dir):
    """ Here we test a PCB with outdated zone fills.
        We run the DRC refilling, but we don't save. """
    ctx = context.TestContext(test_dir, 'DRC_No_Save', 'zone-refill')
    shutil.copy2(ctx.board_file+'.ok', ctx.board_file)
    size = os.path.getsize(ctx.board_file)
    cmd = [PROG, 'run_drc']
    ctx.run(cmd)
    ctx.expect_out_file(REPORT)
    assert os.path.getsize(ctx.board_file) == size
    ctx.clean_up()
