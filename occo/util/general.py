#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

__all__ = ['coalesce', 'icoalesce', 'flatten']

import itertools

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
