#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

import unittest
from common import *
import occo.util.config as cfg

class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.filename = 'test_config.yaml'
        self.ethalon = dict(
            setting_1=1,
            setting_2=2,
            complex_setting=dict(cs_1=3, cs_2=4, cs_3=5),
            list_setting=['a', 'b', 'c']
        )
        with open(self.filename) as f:
            self.args = cfg.DefaultYAMLConfig(f)
    def test_load(self):
        self.args.parse_args()
        self.assertDictContainsSubset(self.ethalon, self.args.__dict__)

class ConfigTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(
            self, map(ConfigTest, ['test_load',
                                   ]))

if __name__ == '__main__':
    alltests = unittest.TestSuite([ConfigTestSuite(),
                                   ])
    unittest.main()
