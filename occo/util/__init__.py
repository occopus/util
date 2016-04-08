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

"""This module contains general utility functions and classes.

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>
"""

__all__ = ['coalesce', 'icoalesce', 'flatten', 'identity',
           'find_effective_setting',
           'Cleaner', 'wet_method',
           'rel_to_file', 'cfg_file_path', 'config_base_dir',
           'set_config_base_dir',
           'path_coalesce', 'file_locations',
           'curried',
           'logged', 'yamldump',
           'f_raise',
           'basic_run_process', 'do_request', 'in_range',
           'HTTPStatusRange',
           'dict_get', 'dict_merge', 'dict_map','Infralist']

import itertools
import logging
import sys
from infralist import *

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

def path_coalesce(*paths):
    """
    Finds the first file in the list that exists.

    :returns: The first existing path or :data:`None`.

    Can be used e.g. for defaulting a config file's path.
    """
    import os
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None

def file_locations(filename, *paths):
    """
    Maps the specified paths to the filenames in a generic way.

    :param str filename: The basename or relative path of a file.
    :param \*args paths: The list of possible base paths for the file.

    :returns: An :func:`iterator <iter>` of the joined paths.

    Each path will be prepended to the filename. The meaning of *prepended* is
    different for different path types.  Currently the following types are
    supported.

        :class:`str`
            Strings are simply ``os.path.join``-ed to the filename.
        :func:`callable`
            The object is called with the filename as a single argument.
        :data:`None`
            Treated the same way as ``''``.
    """
    import os
    for p in paths:
        if callable(p):
            yield p(filename)
        elif isinstance(p, basestring):
            yield os.path.join(p, filename)
        elif p is None:
            yield filename
        else:
            raise NotImplementedError('Unknonw file path definition')

def flatten(iterable):
    """Concatenate several iterables."""
    return itertools.chain.from_iterable(iterable)

def set_config_base_dir(path, use_dir=False, prefix=True):
    """
    Set the global config file base directory.

    A relative path is resolved against the current-previous base directory.
    See :func:`cfg_file_path` for the exact algorithm.

    An absolute path is treated being relative to sys.prefix, unless ``prefix``
    is set to ``False``. This helps "jailing" applications using
    ``cfg_file_path`` inside virtualenvs.

    Note that :func:`cfg_file_path` will not resolve a relative base directory,
    so the behaviour will depend on the caller.

    :param str path: Either the config base path or a file in it (depends on
        ``use_dir``). The path will be normalized based on the CWD.
    :param bool use_dir: Convenience feature: ``path`` refers to a file, use
        the dirname of the path.
    :param bool prefix: If set to ``False``, the absolute path will not be
        resolved/modified.
    """
    global config_base_dir
    if path is None:
        config_base_dir = None
    else:
        import os, sys
        d = os.path.dirname(path) if use_dir else path
        if os.path.isabs(path):
            if prefix:
                d = sys.prefix + d
        else:
            d = cfg_file_path(d)
        config_base_dir = d

config_base_dir = None
"""The base directory for :func:`cfg_file_path`. Default values is the CWD."""

def cfg_file_path(filename, basedir=None):
    """
    Returns the absolute path to ``filename`` based on ``sys.prefix`` and
    ``basedir``.

    If the ``filename`` is absolute, it is treadted being relative to
    ``sys.prefix``.

    A relative ``filename`` will be resolved using a base directory:

        1. The parameter ``basedir``
        2. If ``basedir`` is unset, :data:`config_base_dir`.
        3. If ``config_base_dir`` is unset, then the CWD.

    The base directory path is assumed to be absolute. If it is relative,
    it will not be resolved by this function.

    :param str filename: The path of the configuration file.
    :param str basename: The basedir which ``filename`` is relative to.

    Example::

        with open(occo.util.cfg_file_path('/etc/occo/test.yaml')) as f:
            # Opens (sys prefix)/etc/occo/test.yaml
            cfg = occo.util.config.DefaultYAMLConfig(f)
    """
    import os, sys
    pth = os.path

    if pth.isabs(filename):
        # Using `+` is necessary, as pth.join would simply omit sys.prefix
        # because filename is absolute.
        return pth.abspath(sys.prefix + filename)
    else:
        basedir = coalesce(basedir, config_base_dir, os.getcwd())
        return pth.join(basedir, filename)

def curried(func, **fixed_kwargs):
    """
    A universal closure factory: can be used for `currying
    <http://en.wikipedia.org/wiki/Currying>`_.

    Works only with named arguments. (Possibly with positional arguments too,
    but that is untested.)

    :param callable func: The core function; ``curried`` will return a proxy
        for this callable.
    :param kwargs: Any argument that needs to be preset for the core
        function.
    :returns: A :func:`callable` that acts as a proxy for the core function.
        This proxy will call the core function with the parameter specified
        in ``kwargs``, merged with actual parameters specified upon calling
        the proxy.

    .. code::

        # Example

        def add(x, y):
            return x + y

        add2 = curried(add, x=2)

        add2(y=3) # Equivalent to add(x=2, y=3)

        # More ``real'' example, the curried function used as parameter to
        # other functions:
        # util.file_locations needs callables with a single argument;
        # curried fixes the basefile beforehand.

        possible_locations = list(
            util.file_locations('app.cfg',
                '.',
                util.curried(util.rel_to_file, basefile=__file__),
                util.cfg_file_path))
    """

    import functools
    @functools.wraps(func)
    def proxy(*args, **override_kwargs):
        kwargs = dict(fixed_kwargs)
        kwargs.update(override_kwargs)
        return func(*args, **kwargs)

    return proxy

def rel_to_file(path, basefile=None, d_stack_frame=0, relative_cwd=False):
    """
    Returns the absolute version of ``relpath``, assuming it's relative to the
    given *file* (_not_ directory).

    :param str path: The relative path to be resolved.
    :param str basefile: The base file which ``relpath`` is relative to.
        If unset, ``relpath`` is resolved relative to a caller's ``__file__``
        attribute.
    :param int d_stack_frame: If ``basefile`` is unset, this parameter
        specifies the order of the caller of whose ``__file__`` attribute
        is used. I.e.: If 0, the immediate caller of this function is used. If
        *n*\ >0, the *n*\ th caller in the stack is used.

        With this parameter, libraries can use this function to resolve paths
        relative to *their* caller.

    This function can mainly be used to find files (configuration, resources,
    etc.) relative to the module or executable that is calling it (e.g. test
    modules).
    """
    from os.path import abspath, join, dirname, relpath
    if not basefile:
        # Default base path: path to the caller file
        import inspect
        fr = inspect.currentframe()
        for i in xrange(d_stack_frame+1):
            fr = fr.f_back
        basefile = fr.f_globals['__file__']
    pth = join(dirname(basefile), path)
    return relpath(pth) \
        if relative_cwd \
        else abspath(pth)

def identity(*args):
    """Returns all arguments as-is"""
    if len(args) == 0:
        return None
    elif len(args) == 1:
        return args[0]
    else:
        return tuple(args)

def nothing(*args, **kwargs):
    """Constant function: False"""
    return False

class Cleaner(object):
    """Hide sensitive information if necessary.

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

class wet_method(object):
    """
    Method decorator for classes performing critical operations.
    The wrapped method will _not_ be executed if the object has a member
    ``dry_run`` set to ``True``.
    In this case, a constant default value will be returned.

    :param def_retval: The default value to be returned when the function
        execution is omitted.
    """
    def __init__(self, def_retval=None, dry_run=False):
        self.def_retval = def_retval
        self.dry_run = dry_run

    def __call__(self, fun):
        import functools

        @functools.wraps(fun)
        def wethod(fun_self_, *args, **kwargs):
            log = logging.getLogger('occo.util')
            def sources():
                yield 'object', fun_self_
                yield 'method', self
                yield 'class', fun_self_.__class__
                yield 'module', sys.modules[fun_self_.__class__.__module__]
                yield 'global', sys.modules[__name__]
            def getvalue(o):
                return getattr(o, 'dry_run', False)
            dry_run_set_at = next(
                (src for src, value in pair_map(sources(), getvalue) if value),
                None)
            if dry_run_set_at is not None:
                log.warning('Dry run (specified at %s level): '
                            'omitting method execution for %s.%s.%s',
                            dry_run_set_at,
                            fun_self_.__class__.__module__,
                            fun_self_.__class__.__name__,
                            fun.__name__)
                return self.def_retval
            else:
                return fun(fun_self_, *args, **kwargs)

        return wethod

class global_dry_run(object):
    """
    Context manager for setting and unsetting the global dry_run flag.

    *IMPORTANT:* This is *not* thread safe, one such context will set the flag
    globally (hence the name!). This should only be used in tests, with
    caution.
    """
    def __enter__(self):
        global dry_run
        dry_run = True

    def __exit__(self, *args):
        global dry_run
        dry_run =False

def global_dry_run_set(value):
    global dry_run
    dry_run = value

class logged(object):
    """
    Auxiliary decorator for debugging functions.

    With this decorator, rewriting ``return <<<expression>>>`` statements to
    ``retval = <<<expression>>>; log(retval); return retval`` when debugging
    becomes unecessary.

    The decorator can be disabled; in which case calling the method has no
    overhead.

    :param logger: A logging method of a logging object. E.g.  ``log.debug``.
    :param bool disabled: Disables this decorator. I.e.: when
        disabled, this decorator becomes an identity function.
    :param str prefix: Log record prefix for all generated log records.
    :param str postfix: Log record postfix for all generated log records.

    Logging can be globally enabled by setting ``logged.disabled`` to
    :data:`False`.

    .. warning:: This logging is not secure. Secrets provided for or generated
        by the decorated function are recorded in the logs.

    """

    disabled = True

    def __init__(self, logger_method, disabled=False, prefix='', postfix=''):
        self.logger_method, self.disabled, self.prefix, self.postfix = \
            logger_method, disabled, prefix, postfix

    def __call__(self, fun):
        if logged.disabled or self.disabled:
            return fun

        import functools
        log = self.logger_method

        @functools.wraps(fun)
        def wrapper(*args, **kwargs):
            # Determine whether a method and remove self.
            # inspect.ismethod would not work, as at the time this decorator
            # runs, the function is not yet binded to the class.
            import inspect
            all_args = args
            fun_args = inspect.getargspec(fun).args
            if fun_args and fun_args[0] == 'self':
                args = args[1:] # Remove `self' from output

            funcdef = '[{0}; {1}; {2}]'.format(fun.__name__, args, kwargs)
            log('%sFunction call: %s%s', self.prefix, funcdef, self.prefix)
            retval = fun(*all_args, **kwargs)
            log('%sFunction result: %s -> [%r]%s',
                self.prefix, funcdef, retval, self.prefix)
            return retval

        return wrapper

def yamldump(obj):
    """Shorthand for yaml.dump"""
    import yaml
    return yaml.dump(obj, default_flow_style=False)

def f_raise(ex):
    """
    Method to replace the raise statement so it can be used in lazy expressions
    (``x if B else f_raise(...)``) or (``x or f_raise(...)``).
    """
    raise ex

def basic_run_process(cmd, input_data=None):
    """
    Synchronously run a process and gather its output.

    :param cmd: Either a command line string (will be split at whitespaces) or
        a list of strings serving as argv. E.g. ``['ls', '/etc']``.
    :param input_data: Optional input data for the process.
    :returns: ``$?``, ``stdout``, ``stderr`` of the process.
    """
    log = logging.getLogger('occo.util')

    if isinstance(cmd, basestring):
        cmd = cmd.split()
    import subprocess
    log.debug('Executing subprocess %r', cmd)
    sp = subprocess.Popen(cmd,
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    output = sp.communicate(input_data)
    log.debug('Execution finished, returncode: %d', sp.returncode)
    return sp.returncode, output[0], output[1]

def in_range(n, rng_spec):
    """
    Determines if a number is in the specified range. A tuple is considered an
    inclusive range. A single integer is treated as a one-element interval.
    """
    return (n == rng_spec) if type(rng_spec) is not tuple \
        else (rng_spec[0] <= n <= rng_spec[1])

def in_range_set(n, range_spec):
    """Determines if a number is in any of the ranges listed in ``range_spec``."""
    return any(in_range(n, r) for r in range_spec)

class HTTPStatusRange(object):
    """Semantic HTTP status ranges"""
    CLIENT_ERROR = [(400, 499)]
    SERVER_ERROR = [(500, 599)]
    ALL_ERROR = CLIENT_ERROR + SERVER_ERROR
    NONE = []

def do_request(url, method_name='get',
               auth=None, data=None,
               raise_on=HTTPStatusRange.ALL_ERROR,
               timeout=10,
               allow_redirects=True):
    """
    :param raise_on: List of (tuples or integers) specifying the
        HTTP status codes to be considered exceptional failure.
        Some common ranges are defined in :class:`HTTPStatusRange`.
    :raises: :exc:`requests.exceptions.Timeout`
    :raises: :exc:`requests.exceptions.HTTPError`
    """
    log = logging.getLogger('occo.util')

    import requests

    method = getattr(requests, method_name)

    log.debug('Trying URL %r with method %r', url, method_name)
    r = method(url,
               timeout=timeout,
               auth=auth,
               data=data,
               allow_redirects=allow_redirects)
    log.debug('HTTP response: %d (%s)', r.status_code, r.reason)
    if in_range_set(r.status_code, raise_on):
        r.raise_for_status()
    r.success = in_range(r.status_code, (200, 299))
    return r

def dict_get(mapping, dottedkey):
    """
    Retreives a value from a nesting of dictionaries.

    :param dict mapping: A dictionary that may contain nested dictionaries.
    :param str dottedkey: A dotted nested key specification.

    :raises ValueError: if the key specification, or any of its components is
        empty. E.g. ``""`` or ``"a..c"``.
    :raises KeyError: if the key does not exist.

    E.g.: ``dict_get(x, "a.b.c")`` is equivalent to ``x['a']['b']['c']``.
    """
    return dict_get_lst(mapping, dottedkey.split('.'))

def dict_get_lst(mapping, keylist):
    """
    Retreives a value from a nesting of dictionaries.
    """
    if not keylist:
        raise ValueError('Empty keylist')

    nextkey = keylist[0]
    if not nextkey:
        raise ValueError('Empty key name')

    if len(keylist) == 1:
        return mapping[nextkey]

    sub_mapping = mapping[nextkey]

    try:
        result = dict_get_lst(sub_mapping, keylist[1:])
    except KeyError as e:
        raise KeyError('.'.join([nextkey, e[0]]))
    else:
        return result

def dict_merge(dst, src):
    """
    Merges ``src`` onto ``dst`` in a deep-copied data structure, overriding data
    in ``dst`` with ``src``.

    Both ``dst`` and ``src`` are left intact; and also, they will not share
    objects with the resulting data structure either. This avoids side-effects
    when the result structure is modified, which would cause the original
    ``dst`` to receive modifications if deep copy had not been used.
    """
    import copy

    def rec_merge(dst, src):
        dst = copy.copy(dst)
        for key, val in src.iteritems():
            if (key in dst) and isinstance(val, dict) and isinstance(dst[key], dict):
                dst[key] = rec_merge(dst[key], val)
            else:
                dst[key] = copy.copy(val)
        return dst

    return rec_merge(dst, src)

def pair_map(pairs, value_trans=identity, key_trans=identity):
    return ((key_trans(k), value_trans(v)) for k, v in pairs)
def dict_map(items, value_trans=identity, key_trans=identity):
    """
    Transform dictionary using two transformation functions.

    :param dict items: The dictionary to be transformed.
    :param function value_trans: The transformation to be applied to values.
    :param function key_trans: The transformation to be applied to keys.
    """
    return dict(pair_map(items.iteritems(), value_trans, key_trans))

def find_effective_setting(possibilities, default_none=False):
    """
    Like coalesce, but specifically to find an effective setting.

    :param iterable possibilities: An iterable containing *pairs*: the first
        element is the source of the setting, the second is the value of the
        setting. The value will be tested whether it's specified, the first
        not-None is returned. The source can be used in log files, user
        information, and for debugging.
    :param bool default_none: If ``True``, ``(None, None)`` is returned if none
        of the settings were specified (all ``None``).

    :raises TypeError: if an item is not a pair.
    :raises RuntimeError: if all values are ``None``, and ``default_none`` is
        ``False``.
    """
    for i in possibilities:
        try:
            if i[1] is not None:
                return i
        except IndexError:
            raise TypeError('Wrong item type', i), None, sys.exc_info()[2]

    if not default_none:
        raise RuntimeError('No effective setting found')

    return 'default', None
