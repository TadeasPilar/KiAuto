# -*- coding: utf-8 -*-
# Copyright (c) 2020 Salvador E. Tropea
# Copyright (c) 2020 Instituto Nacional de Tecnologïa Industrial
# License: Apache 2.0
# Project: KiAuto (formerly kicad-automation-scripts)
"""
Tests for eeschema_do bom_xml.

For debug information use:
pytest-3 --log-cli-level debug

"""

import os
import sys
# Look for the 'utils' module from where the script is running
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(script_dir))
# Utils import
from utils import context

PROG = 'eeschema_do'


def test_bom_xml(test_dir):
    prj = 'good-project'
    bom = prj+'.csv'
    ctx = context.TestContextSCH(test_dir, 'BoM_XML', prj)
    cmd = [PROG, '-vv', '-r', '--time_out_scale', '0.9', 'bom_xml']
    ctx.run(cmd)
    ctx.expect_out_file(bom)
    ctx.search_in_file(bom, [r'C1 C2 ,2,"C","Capacitor_SMD:C_0402_1005Metric"',
                             r'P1 ,1,"CONN_01X02","Connector_JST:JST_JWPF_B02B-JWPF-SK-R_1x02_P2.00mm_Vertical"',
                             r'R1 ,1,"R","Resistor_SMD:R_0402_1005Metric"'])
    ctx.clean_up()
