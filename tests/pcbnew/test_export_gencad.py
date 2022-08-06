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
import re
# Look for the 'utils' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
prev_dir = os.path.dirname(script_dir)
sys.path.insert(0, prev_dir)
# Utils import
from utils import context
sys.path.insert(0, os.path.dirname(prev_dir))

PROG = 'pcbnew_do'


def test_export_gencad_1(test_dir):
    """ Generate a GenCAD file with no special options test """
    ctx = context.TestContext(test_dir, 'export_gencad_1', 'good-project')
    cmd = [PROG, '-vv', 'export_gencad', '-f', '-n', '-O', '--output_name', 'good.cad']
    ctx.run(cmd)
    ctx.expect_out_file('good.cad')
    file = ctx.get_out_path('good.cad')
    with open(file, 'rt') as f:
        text = f.read()
    text = re.sub(r'(USER|DRAWING) "(.*)"', r'\1 ""', text)
    with open(file, 'wt') as f:
        f.write(text)
    ctx.compare_txt('good.cad')
    ctx.clean_up()
