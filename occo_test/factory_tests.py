### Copyright 2014, MTA SZTAKI, www.sztaki.hu
###
### Licensed under the Apache License, Version 2.0 (the "License");
### you may not use this file except in compliance with the License.
### You may obtain a copy of the License at
###
###    http://www.apache.org/licenses/LICENSE-2.0
###
### Unless required by applicable law or agreed to in writing, software
### distributed under the License is distributed on an "AS IS" BASIS,
### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
### See the License for the specific language governing permissions and
### limitations under the License.

import unittest
import yaml
import uuid
import occo.exceptions as exc
import occo.util as util
import occo.util.factory as factory

class TestFactory(factory.MultiBackend):
    def __init__(self, a=9):
        self.x = a

@factory.register(TestFactory, 'test')
class TestFactoryImp(TestFactory):
    pass

class CoalesceTest(unittest.TestCase):
    def test_has(self):
        self.assertTrue(TestFactory.has_backend('test'))
        self.assertFalse(TestFactory.has_backend('nonexistent'))
    def test_yaml(self):
        data = util.config.yaml_load_file(
            util.rel_to_file('factory_test.yaml'))
        self.assertIs(type(data['testbackend']), TestFactoryImp)
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
    def test_fromcfg_1(self):
        data = TestFactory.from_config('test') 
        self.assertIs(type(data), TestFactoryImp)
        self.assertEqual(data.x, 9)
    def test_fromcfg_2(self):
        data = TestFactory.from_config(
            dict(
                protocol='test',
                args=[1]
            ))
        self.assertIs(type(data), TestFactoryImp)
        self.assertEqual(data.x, 1)
    def test_fromcfg_3(self):
        with self.assertRaises(ValueError):
            data = TestFactory.from_config(
                dict(
                    protcol='test',
                    args=[1]
                ))
    def test_fromcfg_4(self):
        with self.assertRaises(ValueError):
            data = TestFactory.from_config([1, 2, 3])
