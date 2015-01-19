#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

"""This module contains general utility functions and classes.
"""

__all__ = ['coalesce', 'icoalesce', 'flatten', 'identity',
           'ConfigurationError', 'Cleaner', 'wet_method',
           'rel_to_file', 'cfg_file_path']

import itertools
import logging

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
    """Concatenate several iterables."""
    return itertools.chain.from_iterable(iterable)

def cfg_file_path(filename, basedir='etc/occo'):
    """
    Returns the absolute path to ``filename`` based on ``sys.prefix`` and
    ``basedir``. If ``filename`` is an absolute path, it is returned unchanged.

    Basedir defaults to ``'etc/occo'``.

    Example::

        with open(occo.util.cfg_file_path('test.yaml')) as f:
            # Opens (sys prefix)/etc/occo/test.yaml
            cfg = occo.util.config.DefaultYAMLConfig(f)
    """
    import os, sys
    return \
        filename if os.path.isabs(filename) \
        else os.path.join(sys.prefix, basedir, filename)

def rel_to_file(relpath, basefile=None):
    """
    Returns the absolute version of ``relpath``, assuming it's relative to the
    given file (_not_ directory).

    Default value for ``basefile`` is the ``__file__`` of the caller.

    This function can mainly be used to find files (configuration, resources,
    etc.) relative to the module or executable that is calling it (e.g. test
    modules).
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
    """Cleaner(self, hide_keys=[], hide_values=[], match_hide_keys=nothing, match_hide_values=nothing, bar='XXX')

    Provides a ``deep_copy()`` method that deep-copies a data
    structure (nested lists and dicts), censoring specified information
    (authentication data: passwords, secret keys).

    The actual data is not copied, only the data structure. Data to be censored
    is replaced with a predefined value.

    Censored information are keys ``k`` and values ``v`` for ``(k,v)`` in
    dictionaries and ``v`` in lists:

    - Values pertaining to banned keys
        - ``k in hide_keys``
        - ``match_hide_keys(k)``
    - Values banned explicitly
        - ``v in hide_values``
        - ``match_hide_values(v)``

    ``match_*`` must be callables returning either ``True`` or ``False``.

    :param list hide_keys: Explicit list of keys to be censored.
    :param list hide_values: Explicit list of values to be censored.

    :param match_hide_keys: Boolean function deciding if a key is to
        be censored.
    :type match_hide_keys: ``callable: (any) -> bool``

    :param match_hide_values: Boolean function deciding if a value is to
        be censored.
    :type match_hide_values: ``callable: (any) -> bool``

    :param object bar: The value with which censored data is to be
        substituted.
    """
    def __init__(self,
                 hide_keys=[], hide_values=[],
                 match_hide_keys=nothing, match_hide_values=nothing,
                 bar='XXX'):
        self.hide_keys = hide_keys
        self.hide_values = hide_values
        self.bar = bar
        self.match_hide_keys = match_hide_keys
        self.match_hide_values = match_hide_values

    def hold_back_key(self, key):
        """Decides whether is a key to be censored.

        :param key: The key to be checked.
        :rtype: bool
        """
        return (key in self.hide_keys) or (self.match_hide_keys(key))
    def hold_back_value(self, value):
        """Decides whether is a value to be censored.

        :param value: The value to be checked.
        :rtype: bool
        """
        return (value in self.hide_values) or (self.match_hide_values(value))

    def deep_copy(self, obj):
        """Deep copies a data structure, censoring data if necessary.

        :param obj: The data structure to be copied.
        :type obj: Nested structure of dict and list objects. Any other type of
            object encountered is treated as scalar.
        :return: A copy of ``obj``.
        """
        if type(obj) is dict:
            return self.deep_copy_dict(obj)
        elif type(obj) is list:
            return self.deep_copy_list(obj)
        else:
            return self.deep_copy_value(obj)

    def deep_copy_value(self, value):
        """ Satellite function to :func:`deep_copy` handling scalars. """
        return self.bar if self.hold_back_value(value) else value
    def deep_copy_kvpair(self, first, second):
        """
        Satellite function to :func:`deep_copy` handling key-value pairs in
        a ``dict``.
        """
        return \
            (first, self.bar) \
            if self.hold_back_key(first) or self.hold_back_value(second) \
            else (first, second)

    def deep_copy_dict(self, d):
        """ Satellite function to :func:`deep_copy` handling ``dict`` s. """
        return dict(self.deep_copy_kvpair(k,self.deep_copy(v))
                    for k,v in d.iteritems())
    def deep_copy_list(self, l):
        """ Satellite function to :func:`deep_copy` handling ``list`` s. """
        return [self.bar if self.hold_back_value(i)
                else self.deep_copy(i)
                for i in l]

class WetMethod(object):
    """
    Method decorator for classes performing critical operations.
    The wrapped method will _not_ be executed if the object has a member
    ``dry_run`` set to ``True``.
    In this case, a constant default value will be returned.

    :param def_retval: The default value to be returned when the function
        execution is omitted.
    """

    def __init__(self, def_retval=None):
        self.def_retval = def_retval

    def __call__(self, fun):
        import functools

        @functools.wraps(fun)
        def wethod(fun_self_, *args, **kwargs):
            if fun_self_.dry_run:
                log = logging.getLogger('occo.util')
                log.warning('Dry run: omitting method execution for %s.%s.%s',
                            fun_self_.__class__.__module__,
                            fun_self_.__class__.__name__,
                            fun.__name__)
                return self.def_retval
            else:
                return fun(fun_self_, *args, **kwargs)

        return wethod
wet_method = WetMethod
