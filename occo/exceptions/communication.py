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

"""This module contains OCCO communication-related exceptions.

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>
"""

class CommunicationError(Exception):
    """Raised when a communication error has happened.

    The exception object contains the error code (``http_code``), whose meaning
    is defined by the http standard.

    The exception object may contain a ``reason``, which specifies the details
    of the error.

    RPC clients must be prepared to catch and handle these exceptions.
    """
    def __init__(self, http_code, reason=None):
        self.http_code, self.reason = http_code, reason
    def __str__(self):
        return '[HTTP {0.http_code}] {0.reason}'.format(self)

class TransientError(CommunicationError):
    """A :class:`CommunicationError` that is raised when a transient error occurs.

    E.g.: An internal server error or an 503
    When this exception is raised, the client may retry the request later.
    """
    pass

class CriticalError(CommunicationError):
    """A :class:`CommunicationError` that is raised when an unrecoverable error
    occurs.

    E.g.: A bad request.
    When this exception is raised, the client must not issue the same request
    again.
    """
    pass

import requests
HTTPTimeout = requests.exceptions.Timeout
HTTPError = requests.exceptions.HTTPError
ConnectionError = requests.exceptions.ConnectionError
