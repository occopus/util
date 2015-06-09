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
        self.args = cfg.DefaultYAMLConfig(self.filename)
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
    def test_import(self):
        import yaml
        self.filename = util.rel_to_file('import_test/parent.yaml')
        self.control_filename = util.rel_to_file('import_test/control.yaml')
        data = cfg.yaml_load_file(self.filename)
        print '%r'%data
        self.assertIn('child1', data)
        child1 = data['child1']
        self.assertIs(type(child1), dict)
        self.assertIn('child2', child1)
        child2 = child1['child2']
        self.assertIs(type(child2), dict)
        self.assertIn('dataaa', child2)
        self.assertEqual(child2['dataaa'], 'this is it')
        control = cfg.yaml_load_file(self.control_filename)
        self.assertEqual(data, control)
    def test_import_text(self):
        import yaml
        self.filename = util.rel_to_file('import_test/parent_text.yaml')
        self.control_filename = util.rel_to_file('import_test/control_text.yaml')
        data = cfg.yaml_load_file(self.filename)
        control = cfg.yaml_load_file(self.control_filename)
        self.assertEqual(data, control)
