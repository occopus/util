#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

import unittest
from common import *
import occo.util.config as cfg
import occo.util as util
import sys

class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.filename = util.rel_to_file('test_config.yaml')
        self.ethalon = dict(
            setting_1=1,
            setting_2=2,
            complex_setting=dict(cs_1=3, cs_2=4, cs_3=5),
            list_setting=['a', 'b', 'c']
        )
        with open(self.filename) as f:
            self.args = cfg.DefaultYAMLConfig(f)
    def test_load(self):
        self.args.parse_args('')
        self.assertDictContainsSubset(self.ethalon, self.args.__dict__)
    def test_override(self):
        testargs = '--setting_2=ttt -s1 55'.split()
        self.args.add_argument('--setting_1', '-s1', type=int)
        self.args.add_argument('--setting_2', '-s2')
        self.args.parse_args(testargs)
        self.assertEqual(self.args.setting_1, 55)
        self.assertEqual(self.args.setting_2, 'ttt')
