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

"""This module contains common OCCO InfoBroker exceptions.

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>
"""

class KeyNotFoundError(KeyError):
    """Thrown by :meth:`InfoProvider.get` functions when a given key cannot be
    handled."""
    pass

class ArgumentError(ValueError):
    """Thrown by :meth:`InfoProvider.get` functions when there is an error in
    its arguments."""
    pass
