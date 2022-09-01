# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Salvador E. Tropea
# Copyright (c) 2020-2022 Instituto Nacional de Tecnologïa Industrial
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
"""
Tests for eeschema_do miscellaneous stuff.

For debug information use:
pytest-3 --log-cli-level debug

"""

import logging
import os
import pytest
import sys
# Look for the 'utils' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
prev_dir = os.path.dirname(script_dir)
sys.path.insert(0, prev_dir)
# Utils import
from utils import context
sys.path.insert(0, os.path.dirname(prev_dir))
from kiauto.misc import (EESCHEMA_CFG_PRESENT, KICAD_CFG_PRESENT, NO_SCHEMATIC, WRONG_SCH_NAME, EESCHEMA_ERROR,
                         WRONG_ARGUMENTS)

PROG = 'eeschema_do'
BOGUS_SCH = 'bogus'


def test_eeschema_config_backup(test_dir):
    """ Here we test the extreme situation that a previous run left a config
        back-up and the user must take action. """
    prj = 'good-project'
    ctx = context.TestContextSCH(test_dir, 'Eeschema_config_bkp', prj)
    # Create a fake back-up
    if not os.path.isdir(ctx.kicad_cfg_dir):
        logging.debug('Creating KiCad config dir')
        os.makedirs(ctx.kicad_cfg_dir, exist_ok=True)
    old_config_file = ctx.eeschema_conf + '.pre_script'
    logging.debug('Eeschema old config: '+old_config_file)
    with open(old_config_file, 'wt') as f:
        f.write('Dummy back-up\n')
    # Run the command
    cmd = [PROG, 'run_erc']
    ctx.run(cmd, EESCHEMA_CFG_PRESENT)
    os.remove(old_config_file)
    m = ctx.search_err('Eeschema config back-up found')
    assert m is not None
    ctx.clean_up()


def test_kicad_common_config_backup(test_dir):
    """ Here we test the extreme situation that a previous run left a config
        back-up and the user must take action. """
    prj = 'good-project'
    ctx = context.TestContextSCH(test_dir, 'Eeschema_common_config_bkp', prj)
    # Create a fake back-up
    if not os.path.isdir(ctx.kicad_cfg_dir):
        logging.debug('Creating KiCad config dir')
        os.makedirs(ctx.kicad_cfg_dir, exist_ok=True)
    old_config_file = ctx.kicad_conf + '.pre_script'
    logging.debug('KiCad common old config: '+old_config_file)
    with open(old_config_file, 'wt') as f:
        f.write('Dummy back-up\n')
    # Run the command
    cmd = [PROG, 'run_erc']
    ctx.run(cmd, KICAD_CFG_PRESENT)
    os.remove(old_config_file)
    m = ctx.search_err('KiCad common config back-up found')
    assert m is not None
    ctx.clean_up()


def test_sch_not_found(test_dir):
    """ When the provided .sch isn't there """
    prj = 'good-project'
    ctx = context.TestContextSCH(test_dir, 'Schematic_not_found', prj)
    cmd = [PROG, 'run_erc']
    ctx.run(cmd, NO_SCHEMATIC, filename='dummy')
    m = ctx.search_err(r'ERROR:.* does not exist')
    assert m is not None
    ctx.clean_up()


def test_sch_no_extension(test_dir):
    """ KiCad can't load a schematic file without extension """
    prj = 'good-project'
    ctx = context.TestContextSCH(test_dir, 'SCH_no_extension', prj)
    cmd = [PROG, 'run_erc']
    ctx.run(cmd, WRONG_SCH_NAME, filename='Makefile')
    m = ctx.search_err(r'Input files must use an extension')
    assert m is not None
    ctx.clean_up()


def test_bogus_sch(test_dir):
    """ A broken SCH file """
    ctx = context.TestContextSCH(test_dir, 'Bogus_SCH', 'good-project')
    # Current KiCad 5.99 (20201125) creates the warning dialog, but doesn't give it focus.
    # So we never know about the problem.
    sch = ctx.get_out_path(BOGUS_SCH+ctx.sch_ext)
    # Create an invalid SCH
    with open(sch, 'w') as f:
        f.write('dummy')
    cmd = [PROG, '-vv', '-r', 'run_erc']
    ctx.run(cmd, EESCHEMA_ERROR, filename=sch)
    if context.ki5:
        assert ctx.search_err(r"eeschema reported an error") is not None
    else:
        assert (ctx.search_err(r"ERROR:Error loading schematic file") or
                ctx.search_err(r"ERROR:Eeschema created an error dialog")) is not None
    ctx.clean_up()


def test_sch_wrong_command(test_dir):
    """ Wrong command line arguments """
    ctx = context.TestContextSCH(test_dir, 'SCH_Wrong_Command', 'good-project')
    cmd = [PROG, 'bogus']
    ctx.run(cmd, WRONG_ARGUMENTS)
    ctx.clean_up()


def test_time_out(test_dir):
    """ ERC time-out """
    ctx = context.TestContextSCH(test_dir, 'SCH_Time_Out', 'good-project')
    cmd = [PROG, '--time_out_scale', '0', 'run_erc']
    ctx.run(cmd, 1)
    ctx.clean_up()


@pytest.mark.skipif(context.ki5, reason="Test for KiCad 6 dialog")
def test_miss_wks_sch(test_dir):
    """ Missing kicad_wks """
    prj = 'missing-project'
    net = prj+'.net'
    ctx = context.TestContextSCH(test_dir, 'Missing_WKS_SCH', prj)
    # Force removing the .net
    ctx.create_dummy_out_file(net)
    cmd = [PROG, '-vvv', 'netlist']
    ctx.run(cmd)
    ctx.expect_out_file(net)
    ctx.clean_up()
