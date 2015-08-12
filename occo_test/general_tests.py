#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

import unittest
import yaml
import uuid, requests.exceptions as exc
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

    def test_curried(self):
        cu = util.curried
        def add(x, y):
            return x+y
        self.assertEqual(cu(add, y=2)(2), 4)

    def test_identity(self):
        i = util.identity
        self.assertIsNone(i())
        self.assertIsNone(i(None))
        self.assertEquals(i(1), 1)
        x, y, z = i(1, 2, 3)
        self.assertEquals((x, y, z), (1, 2, 3))

    def test_nothing(self):
        self.assertFalse(util.nothing())

    def test_cleaner(self):
        c = util.Cleaner(hide_keys=['pass'], hide_values=['xyz', 'zyx'])
        _in = yaml.load("""
                        pass: alma
                        password: xyz
                        public: yaay
                        stuff:
                            -
                                secret: zyx
                            -
                                - zyx
                                - alma
                        """)
        _out = yaml.load("""
                         pass: XXX
                         password: XXX
                         public: yaay
                         stuff:
                            -
                                secret: XXX
                            -
                                - XXX
                                - alma
                         """)
        obfuscated = c.deep_copy(_in)
        self.assertEqual(obfuscated, _out)

    def test_wethod(self):
        class WC(object):
            def __init__(self, dr):
                self.dry_run = dr
            @util.wet_method(1)
            def wc(self, x):
                return x
        self.assertEqual(WC(False).wc(5), 5)
        self.assertEqual(WC(True).wc(5), 1)

    def test_logged_function(self):
        items = list()
        def setx(fmt, *args):
            items.append(fmt%tuple(args))

        util.logged.disabled = False

        @util.logged(setx)
        def fun(x, y):
            return x+y

        fun(1, 2)
        self.assertEqual(items,
                         [
                             'Function call: [fun; (1, 2); {}]',
                             'Function result: [fun; (1, 2); {}] -> [3]'
                         ])

    def test_logged_method(self):
        items = list()
        def setx(fmt, *args):
            items.append(fmt%tuple(args))

        util.logged.disabled = False

        class A(object):
            @util.logged(setx)
            def fun(self, x, y):
                return x+y

        A().fun(1, 2)
        self.assertEqual(items,
                         [
                             'Function call: [fun; (1, 2); {}]',
                             'Function result: [fun; (1, 2); {}] -> [3]'
                         ])

    def test_yaml_dump(self):
        # Only a wrapper for yaml.dump, so the test is only for coverage
        util.yamldump(dict(a=1, b=2))

    def test_f_raise(self):
        with self.assertRaises(Exception):
           util.f_raise(Exception())

    def test_run_process(self):
        data='stuffstuff'
        rc, stdout, stderr = util.basic_run_process('cat', data)
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, data)

    @unittest.skip("Skipping slow test of util.do_request")
    def test_do_request(self):
        dr = util.do_request
        r = dr('http://example.org/', method_name='head')
        self.assertTrue(r.success)
        rndstr = str(uuid.uuid4())
        with self.assertRaises(exc.HTTPError):
            r = dr('http://google.com/{0}'.format(rndstr), method_name='head')

    def test_dict_get(self):
        dg = util.dict_get
        dgl = util.dict_get_lst
        data = yaml.load("""
                         a:
                            b:
                                c:
                                    d
                         b:
                            x
                         """)
        self.assertEqual(dg(data, 'a.b.c'), 'd')
        with self.assertRaises(ValueError):
            dgl(data, [])
        with self.assertRaises(ValueError):
            dg(data, 'a..b')
        with self.assertRaises(KeyError):
            dg(data, 'a.c.c')

    def test_dict_merge(self):
        d1 = dict(a=1, b=dict(c=2, d=3), e=4)
        d2 = dict(b=dict(c=10, f=11), e=dict(g=12))
        dexp = dict(a=1, b=dict(c=10, d=3, f=11), e=dict(g=12))

        dres = util.dict_merge(d1, d2)
        self.assertEqual(dexp, dres)

    def test_find_effective_setting(self):
        def testsettings():
            yield 'a', None
            yield 'b', 1
            yield 'c', 2

        def badsettings():
            yield 'a', None
            yield 'b', None
            yield 'c', None

        with self.assertRaises(TypeError):
            util.find_effective_setting([None, None, 2])
        with self.assertRaises(RuntimeError):
            util.find_effective_setting(badsettings())
        s, d = util.find_effective_setting(badsettings(), True)
        self.assertEqual((s, d), ('default', None))
        s, d = util.find_effective_setting(testsettings(), True)
        self.assertEqual((s, d), ('b', 1))
