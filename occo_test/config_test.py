#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

import unittest
import occo.util.config as cfg
import occo.util as util
import occo.exceptions
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
    def test_import_from_string(self):
        import yaml
        util.set_config_base_dir(util.rel_to_file('import_test'),
                                 prefix=False)
        self.control_filename = util.rel_to_file('import_test/control_text.yaml')
        data = yaml.load("""
                         nothing: 0
                         child1: !text_import
                             url: file://c1_text.yaml
                         """)
        control = cfg.yaml_load_file(self.control_filename)
        self.assertEqual(data, control)
    def test_cfg_repr(self):
        # No functional test; only for coverage
        repr(self.args)
        str(self.args)
    def test_cfg_args(self):
        cfg = util.config.config
        c = cfg(args=['--cfg',
                      util.rel_to_file('comm_test_cfg.yaml',
                                       relative_cwd=True)])
    def test_cfg_param(self):
        cfg = util.config.config
        c = cfg(cfg_path=util.rel_to_file('comm_test_cfg.yaml',
                                          relative_cwd=True),
                args=[])
    def test_cfg_error(self):
        cfg = util.config.config
        with self.assertRaises(occo.exceptions.ConfigurationError):
            try:
                c = cfg(args=[])
            except occo.exceptions.ConfigurationError as e:
                print str(e)
                raise
