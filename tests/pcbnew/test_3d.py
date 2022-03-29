# -*- coding: utf-8 -*-
# Copyright (c) 2021 Salvador E. Tropea
# Copyright (c) 2021 Instituto Nacional de Tecnologïa Industrial
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
"""
Tests for 'pcbnew_do 3d_view'

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


def test_3d_view_1(test_dir):
    """ Simple 3D Viewer test """
    ctx = context.TestContext(test_dir, '3DView_1', 'good-project')
    cmd = [PROG, '-vvv', '3d_view', '--zoom', '3', '-x', '1', '--output_name', 'good_3d_rt_1.png', '-r', '-d', '-w', '600',
           '-X', '3', '-Z', '3']
    ctx.run(cmd)
    ctx.compare_image('good_3d_rt_1.png', fuzz='50%')
    ctx.clean_up()


def test_3d_view_2(test_dir):
    """ Simple 3D Viewer test """
    ctx = context.TestContext(test_dir, '3DView_2', 'good-project')
    cmd = [PROG, '-vvv', '3d_view', '--zoom', '6', '-x', '-1', '--output_name', 'good_3d_rt_2.png', '--no_smd', '-r', '-O',
           '-d', '-w', '600']
    ctx.run(cmd)
    ctx.compare_image('good_3d_rt_2.png', fuzz='50%')
    ctx.clean_up()
