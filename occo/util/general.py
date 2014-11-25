#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

__all__ = ['coalesce', 'icoalesce', 'flatten', 'identity',
           'ConfigurationError', 'Cleaner', 'wet_method',
           'rel_to_file']

import itertools

class ConfigurationError(Exception):
    """Raised by communication classes, if the given configuration is bad, or
    insufficient."""
    pass

def icoalesce(iterable, default=None):
    """Returns the first non-null element of the iterable.

    If there is no non-null elements in the iterable--or the iterable is
    empty--the default value is returned.

    If the value to be returned is an exception object, it is raised instead.
    """
    result = next((i for i in iterable if i is not None), default)
    if isinstance(result, Exception):
        raise result
    return result
def coalesce(*args):
    """Proxy function for icoalesce. Provided for convenience."""
    return icoalesce(args)
def flatten(iterable):
    return itertools.chain.from_iterable(iterable)

def rel_to_file(relpath, basefile=None):
    """
    Returns the absolute version of relpath, assuming it's relative to the
    given file (_not_ directory).
    Default value for `basefile` is the __file__ of the caller.
    """
    from os.path import abspath, join, dirname
    if not basefile:
        # Default base path: path to the caller file
        import inspect
        basefile = inspect.currentframe().f_back.f_globals['__file__']
    return abspath(join(dirname(basefile), relpath))

def identity(*args):
    """Returns all arguments as-is"""
    return tuple(args)

def nothing(*args, **kwargs):
    """Constant function: False"""
    return False

class Cleaner(object):
    """
    Provides a deep_copy() method that deep-copies a data
    structure (nested lists and dicts), censoring specified information.

    Censored information are:
    - values pertaining to banned keys:
        - k in hide_keys
        - match_hide_keys(k)
    - values banned explicitly
        - v in hide_values
        - match_hide_values(v)

    match_* must be callables returning either True or False.
    """
    def __init__(self,
                 hide_keys=[],
                 hide_values=[],
                 match_hide_keys=nothing,
                 match_hide_values=nothing,
                 bar='XXX'):
        self.hide_keys = hide_keys
        self.hide_values = hide_values
        self.bar = bar
        self.match_hide_keys = match_hide_keys
        self.match_hide_values = match_hide_values

    def hold_back_key(self, key):
        return (key in self.hide_keys) or (self.match_hide_keys(key))
    def hold_back_value(self, value):
        return (value in self.hide_values) or (self.match_hide_values(value))

    def deep_copy(self, obj):
        if type(obj) is dict:
            return self.deep_copy_dict(obj)
        elif type(obj) is list:
            return self.deep_copy_list(obj)
        else:
            return self.deep_copy_value(obj)

    def deep_copy_value(self, value):
       return self.bar if self.hold_back_value(value) else value
    def deep_copy_kvpair(self, first, second):
        return \
            (first, self.bar) \
            if self.hold_back_key(first) or self.hold_back_value(second) \
            else (first, second)

    def deep_copy_dict(self, d):
        return dict(self.deep_copy_kvpair(k,self.deep_copy(v))
                    for k,v in d.iteritems())
    def deep_copy_list(self, l):
        return [self.bar if self.hold_back_value(i)
                else self.deep_copy(i)
                for i in l]

class WetMethod(object):
    """
    Method decorator for classes performing critical operations.
    The wrapped method will _not_ be executed if the object has a member
    `dry_run' set to true.
    In this case, a constant default value will be returned.
    """

    def __init__(self, def_retval=None):
        self.def_retval = def_retval

    def __call__(self, fun):
        import functools

        @functools.wraps(fun)
        def wethod(fun_self_, *args, **kwargs):
            if fun_self_.dry_run:
                return self.def_retval
            else:
                return fun(fun_self_, *args, **kwargs)

        return wethod
wet_method = WetMethod
