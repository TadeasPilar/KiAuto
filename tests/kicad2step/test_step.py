# -*- coding: utf-8 -*-
# Copyright (c) 2022 Salvador E. Tropea
# Copyright (c) 2022 Instituto Nacional de Tecnologïa Industrial
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
"""
Tests for kicad2step

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
# Look for the 'utils' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
prev_dir = os.path.dirname(script_dir)
sys.path.insert(0, prev_dir)
# Utils import
from utils import context
sys.path.insert(0, os.path.dirname(prev_dir))

PROG = 'kicad2step_do'


def test_kicad2step_1(test_dir):
    fname = 'good.step'
    fdir = os.path.join(test_dir, 'STEP_1')
    ctx = context.TestContext(test_dir, 'STEP_1', 'good-project')
    os.environ['KIPRJMOD'] = os.path.dirname(ctx.board_file)
    cmd = [PROG, '-vvv', '-o', fname, '-d', fdir, '--subst-models']
    ffname = os.path.join(fdir, fname)
    if os.path.isfile(ffname):
        os.remove(ffname)
    ctx.run(cmd, no_dir=True)
    del os.environ['KIPRJMOD']
    ctx.expect_out_file(fname)
    ctx.clean_up()
