# -*- coding: utf-8 -*-
# Copyright (c) 2022 Theo Hussey
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
"""
Tests for 'pcbnew_do export_gencad'

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

PROG = 'pcbnew_do'


def test_export_gencad(test_dir):
    """ Generate a GenCAD file with no special options test """
    ctx = context.TestContext(test_dir, 'export_gencad', 'good-project')
    cmd = [PROG, 'export_gencad', '--output_name', 'good.cad']
    ctx.run(cmd)
    ctx.expect_out_file('good.cad')
    ctx.clean_up()
