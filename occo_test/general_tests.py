#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

import unittest

import occo.util as util

class DummyException(Exception):
    pass

class CoalesceTest(unittest.TestCase):
    def test_i_empty(self):
        self.assertIsNone(util.icoalesce([]))
    def test_i_default(self):
        self.assertEqual(util.icoalesce([], 5), 5)
    def test_i_first(self):
        self.assertEqual(util.icoalesce(('first', None, 'third')), 'first')
    def test_i_third(self):
        self.assertEqual(util.icoalesce((None, None, 'third')), 'third')
    def test_i_error(self):
        with self.assertRaises(DummyException):
            return util.icoalesce((None, None, None), DummyException(':P'))
    def test_empty(self):
        self.assertIsNone(util.coalesce())
    def test_first(self):
        self.assertEqual(util.coalesce('first', None, 'third'), 'first')
    def test_third(self):
        self.assertEqual(util.coalesce(None, None, 'third'), 'third')
    def test_error(self):
        with self.assertRaises(DummyException):
            return util.coalesce(None, None, None, DummyException(':P'))
    def test_flatten(self):
        l1, l2, l3 = [0, 1, 2, 3], [], [4, 5, 6]
        self.assertEqual(list(util.flatten([l1, l2, l3])), range(7))
    def test_rel_to_file(self):
        # TODO 1) this is not a test
        #      2) need to test d_stack_frame too
        print util.rel_to_file('test.yaml')
    def test_cfg_path1(self):
        import sys, os
        # Reset config path
        util.set_config_base_dir(None)
        self.assertEqual(util.cfg_file_path('alma'),
                         os.path.join(os.getcwd(), 'alma'))
    def test_cfg_path2(self):
        import sys, os
        # Reset config path
        util.set_config_base_dir(None)
        self.assertEqual(util.cfg_file_path('alma', '/etc/occo'),
                         os.path.join('/etc/occo', 'alma'))
    def test_cfg_path3(self):
        import sys, os
        util.set_config_base_dir('/etc/occo', prefix=False)
        self.assertEqual(util.cfg_file_path('alma'),
                         '/etc/occo/alma')
    def test_cfg_path4(self):
        import sys, os
        util.set_config_base_dir('/etc/occo')
        self.assertEqual(util.cfg_file_path('alma', '/etc/occo2'),
                         '/etc/occo2/alma')
    def test_cfg_path5(self):
        import sys, os
        # Reset config path
        util.set_config_base_dir(None)
        self.assertEqual(util.cfg_file_path('/etc/occo/alma'),
                         sys.prefix + '/etc/occo/alma')
    def test_cfg_path6(self):
        import sys, os
        # Reset config path
        util.set_config_base_dir(None)
        self.assertEqual(util.cfg_file_path('/etc/occo/alma', 'anyth:ng'),
                         sys.prefix + '/etc/occo/alma')
    def test_cfg_path7(self):
        import sys, os
        # Reset config path
        util.set_config_base_dir(None)
        util.set_config_base_dir('etc/occo', prefix=False)
        self.assertEqual(util.cfg_file_path('alma'),
                         os.path.join(os.getcwd(), 'etc/occo/alma'))

    def test_path_coalesce(self):
        pc = util.path_coalesce
        self.assertIsNone(pc())
        self.assertIsNone(pc(None, None, None))
        self.assertIsNone(pc('nonexistentfile'))
        self.assertEqual(pc(None, __file__), __file__)

    def test_file_locations(self):
        fl = util.file_locations
        self.assertEqual(
            list(
                fl('x', None, '', 'y', lambda x: x+x)),
            ['x', 'x', 'y/x', 'xx'])
