# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnologïa Industrial
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
"""
Tests for pcbnew_do miscellaneous stuff

For debug information use:
pytest-3 --log-cli-level debug

"""

import pytest
import os
import sys
import logging
# Look for the 'utils' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
prev_dir = os.path.dirname(script_dir)
sys.path.insert(0, prev_dir)
# Utils import
from utils import context
sys.path.insert(0, os.path.dirname(prev_dir))
from kiauto.misc import (PCBNEW_CFG_PRESENT, NO_PCB, WRONG_PCB_NAME, WRONG_ARGUMENTS, CORRUPTED_PCB)

PROG = 'pcbnew_do'
BOGUS_PCB = 'bogus.kicad_pcb'


def test_pcbnew_config_backup(test_dir):
    """ Here we test the extreme situation that a previous run left a config
        back-up and the user must take action. """
    prj = 'good-project'
    ctx = context.TestContext(test_dir, 'PCBnew_config_bkp', prj)
    # Create a fake back-up
    if not os.path.isdir(ctx.kicad_cfg_dir):
        logging.debug('Creating KiCad config dir')
        os.makedirs(ctx.kicad_cfg_dir, exist_ok=True)
    old_config_file = ctx.pcbnew_conf + '.pre_script'
    logging.debug('PCBnew old config: '+old_config_file)
    with open(old_config_file, 'wt') as f:
        f.write('Dummy back-up\n')
    # Run the command
    try:
        cmd = [PROG, 'run_drc']
        ctx.run(cmd, PCBNEW_CFG_PRESENT)
    finally:
        os.remove(old_config_file)
    m = ctx.search_err('PCBnew config back-up found')
    assert m is not None
    ctx.clean_up()


def test_pcb_not_found(test_dir):
    """ When the provided .kicad_pcb isn't there """
    prj = 'good-project'
    ctx = context.TestContext(test_dir, 'PCB_not_found', prj)
    cmd = [PROG, 'run_drc']
    ctx.run(cmd, NO_PCB, filename='dummy')
    m = ctx.search_err(r'ERROR:.* does not exist')
    assert m is not None
    ctx.clean_up()


def test_pcb_no_extension(test_dir):
    """ KiCad can't load a PCB file without extension """
    prj = 'good-project'
    ctx = context.TestContext(test_dir, 'PCB_no_extension', prj)
    cmd = [PROG, 'run_drc']
    ctx.run(cmd, WRONG_PCB_NAME, filename='Makefile')
    m = ctx.search_err(r'Input files must use an extension')
    assert m is not None
    ctx.clean_up()


def test_bogus_pcb(test_dir):
    """ A broken PCB file """
    ctx = context.TestContext(test_dir, 'Bogus_PCB', 'good-project')
    pcb = ctx.get_out_path(BOGUS_PCB)
    # Create an invalid PCB
    with open(pcb, 'w') as f:
        f.write('dummy')
    cmd = [PROG, '--wait_start', '5', 'run_drc']
    ctx.run(cmd, CORRUPTED_PCB, filename=pcb)
    assert ctx.search_err(r"Error loading PCB file. Corrupted?") is not None
    ctx.clean_up()


def test_pcb_wrong_command(test_dir):
    """ Wrong command line arguments """
    ctx = context.TestContext(test_dir, 'PCB_Wrong_Command', 'good-project')
    cmd = [PROG, 'bogus']
    ctx.run(cmd, WRONG_ARGUMENTS)
    ctx.clean_up()


@pytest.mark.skipif(context.ki5, reason="Test for KiCad 6 dialog")
def test_miss_wks_pcb(test_dir):
    """ Missing kicad_wks """
    prj = 'missing-project'
    net = prj+'.d356'
    ctx = context.TestContext(test_dir, 'Missing_WKS_PCB', prj)
    cmd = ['pcbnew_do', '-vv', 'ipc_netlist', '-o', net]
    ctx.run(cmd)
    ctx.expect_out_file(net)
    ctx.clean_up()
