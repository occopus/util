#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

__all__ = ['coalesce', 'icoalesce', 'flatten', 'identity',
           'ConfigurationError']

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

def identity(*args):
    """Returns all arguments as-is"""
    return tuple(args)

def nothing(*args, **kwargs):
    """Identity function: False"""
    return False

class Cleaner(object):
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
    def deep_copy_value(self, value):
       return self.bar if self.hold_back_value(value) else value
    def deep_copy_pair(self, first, second):
        return (first, self.bar) \
            if self.hold_back_key(first) or self.hold_back_value(second) \
            else (first, second)

    def deep_copy_dict(self, d):
        return dict(deep_copy_pair(k,v) for k,v in d.iteritems())
    def deep_copy_list(self, l):
        return [self.bar if self.hold_back_value(i) else i
                for i in l]

