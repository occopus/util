#
# Copyright (C) 2014 MTA SZTAKI
#

"""This module contains common OCCO exceptions.

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>
"""

from __future__ import absolute_import

from .infobroker import *
from .communication import *

class ConfigurationError(Exception):
    """Raised by communication classes, if the given configuration is bad, or
    insufficient."""
    pass

class SchemaError(Exception):
    """Exception representing a schema error in the input data."""
    pass
