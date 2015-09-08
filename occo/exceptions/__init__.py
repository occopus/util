#
# Copyright (C) 2014 MTA SZTAKI
#

"""This module contains common OCCO exceptions.

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>
"""

from __future__ import absolute_import

from .infobroker import *
from .communication import *
from .api import *
from .orchestration import *

class ConfigurationError(Exception):
    """Raised when a given configuration is bad, or insufficient."""
    pass

class MissingConfigurationError(ConfigurationError):
    """Raised when a configuration item is missing and has no default."""
    pass

class AutoImportError(ConfigurationError):
    """Raised when ``!python_import`` fails."""
    def __str__(self):
        return (
            "Error importing '{module_name}' referenced "
            "in '{filename}': {reason}".format(
                filename=self.args[0],
                module_name=self.args[1],
                reason=self.args[2],
            )
        )

class SchemaError(Exception):
    """Exception representing a schema error in the input data."""
    pass
