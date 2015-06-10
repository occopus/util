#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

import unittest
import yaml
import uuid
import occo.exceptions as exc
import occo.util as util
import occo.util.factory as factory

class TestFactory(factory.MultiBackend):
    def __init__(self, a):
        self.x = a

@factory.register(TestFactory, 'test')
class TestFactoryImp(TestFactory):
    pass

class CoalesceTest(unittest.TestCase):
    def test_yaml(self):
        data = util.config.yaml_load_file(
            util.rel_to_file('factory_test.yaml'))
        self.assertTrue(type(data['testbackend']) is TestFactoryImp)
        self.assertEqual(data['testbackend'].x, 1)
    def test_errors(self):
        with self.assertRaises(exc.ConfigurationError):
            yaml.load("""
                      testbackend: !TestFactory
                          a: 1
                      """)
        with self.assertRaises(exc.ConfigurationError):
            yaml.load("""
                      testbackend: !TestFactory
                          protocol: nonexistent
                          a: 1
                      """)
