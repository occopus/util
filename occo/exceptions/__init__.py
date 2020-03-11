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

"""This module contains common OCCO exceptions.

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>
"""



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
    def __init__(self, msg, context=None,*args):
            Exception.__init__(self, *args)
            self.msg = msg
            self.context = context
    def __str__(self):
            return repr(self.msg)
