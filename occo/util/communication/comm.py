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

""" Communication primitives for the SZTAKI Cloud Orchestrator

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>

This module contains the abstract interfaces that are used by the OCCO
components. All abstract interfaces must be implemented by backends (actual
implementations) in other modules. Each backend must be registered, so
selecting and instantiating the right backend can be done automatically.

.. todo:: Refactor: extract errors to dedicated error module.
"""

__all__ = ['AsynchronProducer', 'RPCProducer', 'EventDrivenConsumer',
           'CommChannel',
           'Response', 'ExceptionResponse']

import occo.util.factory as factory
from occo.exceptions import TransientError, CriticalError

class Response(object):
    """RPC services will return a ``Response`` object containing the response
    data and response status information.

    A ``Response`` object can check itself, and raise an exception based on
    its status code.

    :param int http_code: The HTTP code for the response. The :func:`check` 
        method processes this information and raises an exception as necessary
        (see: :class:`CriticalError` and :class:`TransientError`).

    :param data: The content of the response.

    :param bool finalize: Determines whether the RPC request has been actually
        processed, and should be finalized. If ``True``, the request should be
        marked as processed, and processing must not be repeated.  If set to
        ``False``, processing has been aborted, and may be retried at a later
        time, possibly by another server instance. This functionality should be
        implemented by backends.

    .. note::

        RPC *clients* need not bother with ``Response`` objects, the
        communication layer will hide it.

        However, the *server* core function has to return a ``Response`` object
        containing an http code and data. If an exception has to be raised on
        client side, an :class:`ExceptionResponse` object should be returned.

        Calling ``push_message`` on client side will either return the raw
        response data, or raise the exception thrown by the server code. It
        will never see the original response object.

    .. warning::

        The server-side behaviour may change in the future. The goal would
        be to make the server core function oblivious to communication details.
        However, it is hard to distinguish between exceptions that should be
        returned to the client, and those that should not (500 Internal
        Server Error). If there is a solution, we will try and find it.
    """
    def __init__(self, http_code, data, finalize=True):
        self.http_code, self.data = http_code, data
        self.finalize = finalize

    def check(self):
        """Raises an exception based on the status code of the response."""
        code = self.http_code
        if code <= 199:
            raise NotImplementedError()
        elif code <= 299:
            pass
        elif code <= 399:
            raise NotImplementedError()
        elif code <= 499:
            raise CriticalError(code, self.data)
        elif code <= 599:
            raise TransientError(code, self.data)
        else:
            raise NotImplementedError()

class ExceptionResponse(Response):
    """Special :class:`Response` that will only raise an internal exception."""
    def check(self):
        raise self.data

class CommChannel(object):
    """Abstraction of a communication channel.
    
    This interface defines a communication channel. Currently we need three
    services from such a channel: encoding and decoding a data object to
    be transmitted over the channel, and sending an encoded message through
    the channel.
    """
    def serialize(self, obj):
        """Create a transmittable representation of ``obj``."""
        raise NotImplementedError()

    def deserialize(self, repr_):
        """Create an object from its representation."""
        raise NotImplementedError()

    def push_message(self, message, **kwargs):
        """Push a message to the channel."""
        raise NotImplementedError()

class AsynchronProducer(factory.MultiBackend, CommChannel):
    """Abstract interface of an asynchronous producer. Sub-classes must
    implement asynchron message pushing in the :meth:`push_message` method."""
    def push_message(self, message, **kwargs):
        """Asynchron message pushing.

        This method returns ``None``, or only control responses (ACK,
        :class:`Exception`, etc.). This method should not return the result of
        the operation as it is performed asynchronously.
        """
        raise NotImplementedError()

class RPCProducer(factory.MultiBackend, CommChannel):
    """Abstract interface of an RPC client. Sub-classes must implement remote
    procedure calls in the :meth:`push_message` method.

    Sub-classes should implement higher level abstraction for method calling;
    i.e. provide semantic methods that are implemented using :meth:`push_message`.
    """
    def push_message(self, message, **kwargs):
        """Synchronous message pushing.

        This method sends a message or request to the remote entity, and
        returns the result of the operation (or raises an exception).

        When using an ``RPCProducer``, the client must expect this function to
        hang up the execution while it waits for a response.

        Sub-classes must implement timouts as necessary.
        """
        raise NotImplementedError

class EventDrivenConsumer(factory.MultiBackend, CommChannel):
    """Abstract interface of an event-driven message processor.

    Sub-classes must implement the :meth:`start_consuming` method, which should
    call :meth:`_call_processor` whenever a message arrives.

    A Sub-class may also implement the ``processor`` function itself, so it
    can act as a self-contained service.

    :param processor: The core function to be called when a message arrives,
        with the following arguments:

        ============  ==================================================
        Parameter     Description
        ============  ==================================================
        ``message``   The content of the message
        ------------  --------------------------------------------------
        ``...``       Backend-specific arguments, *iff* specified by the
                      sub-class. Sub-classes must override the
                      :meth:`_call_processor` method to achieve this.
        ------------  --------------------------------------------------
        ``*args``     ``self.pargs``
        ------------  --------------------------------------------------
        ``**kwargs``  ``self.pkwargs``
        ============  ==================================================

    :type processor: :func:`callable` ``(message, [...,] *args, **kwargs)``

    :param list pargs: List of arguments to be passed to the registered
        function as ``*args``.
    
    :param dict kwargs: A dictionary to be passed to the registered function as
        ``**kwargs``.

    ..
        Explicitly needed for Sphinx to render _call_processor docstring,
        because of the leading underscore:
    .. automethod:: _call_processor
    """
    def __init__(self, processor, pargs=[], pkwargs={}, **config):
        self.processor, self.pargs, self.pkwargs = \
            processor, pargs, pkwargs
    def _call_processor(self, data):
        """Calls the message processor function with the proper arguments
        specified in the class documentation (:class:`EventDrivenConsumer`)."""
        return self.processor(data, *self.pargs, **self.pkwargs)
    def start_consuming(self):
        """Start consuming messages in an infinite loop."""
        raise NotImplementedError
