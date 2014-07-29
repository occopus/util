#
# Copyright (C) 2014 MTA SZTAKI
#
# Communication primitives for the SZTAKI Cloud Orchestrator
#

"""This module contains the abstract interfaces that are used by the OCCO
components. All abstract interfaces must be implemented by backends (actual
implementations) in other modules. Each backend must be registered, so
selecting and instantiating the right backend can be done automatically.
"""

__all__ = ['AsynchronProducer', 'RPCProducer', 'EventDrivenConsumer',
           'register', 'CommChannel',
           'ConfigurationError',
           'CommunicationError', 'TransientError', 'CriticalError',
           'Response', 'ExceptionResponse']

class ConfigurationError(Exception):
    """Raised by communication classes, if the given configuration is bad, or
    insufficient."""
    pass

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
        return '[HTTP %d] %s'%(self.http_code, self.reason)

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

class Response(object):
    """RPC services will return a ``Response`` object containing the response
    data and response status information.

    A ``Response`` object can check itself, and raise an exception based on
    its status code.

    .. note::

        RPC clients need not bother with ``Response`` objects, the
        communication layer will hide it.

        The server core functionhas to return a Response object containing
        an http code and data. If an exception has to be raised on client side,
        an :class:`ExceptionResponse` object should be returned.

        Calling ``push_message`` on client side will either return the raw
        response data, or raise the exception thrown by the server code.

    .. warning::

        The server-side behaviour may change in the future. The goal would
        be to make the server core function oblivious to communication details.
        However, it is hard to distinguish between exceptions that should be
        returned to the client, and those that should not (500 Internal
        Server Error). If there is a solution, we will try and find it.
    """
    def __init__(self, http_code, data):
        self.http_code, self.data = http_code, data
    def check(self):
        """Raises an exception based on the status code of the response."""
        code = self.http_code
        if code <= 199: raise NotImplementedError()
        elif code <= 299: pass
        elif code <= 399: raise NotImplementedError()
        elif code <= 499: raise CriticalError(code, self.data)
        elif code <= 599: raise TransientError(code, self.data)
        else: raise NotImplementedError()

class ExceptionResponse(Response):
    """Special response that will only raise an internal exception."""
    def check(self):
        raise self.data

class RegisteredBackend(object):
    """Decorator class to register backends for the communication classes.

    target: the target primitive, of which the decorated class is an
            implementation
    id_:    protocol identifier; an arbitrary string that identifies the
            set of backends
    """
    def __init__(self, target, id_):
        self.target = target
        self.id_ = id_
    def __call__(self, cls):
        if not hasattr(self.target, 'backends'):
            self.target.backends = dict()
        self.target.backends[self.id_] = cls
        return cls
register = RegisteredBackend

class MultiBackend(object):
    """Meta-class that automates backend selection based on configuration
    parameters.

    Raises ConfigurationError, if `protocol' is not specified, or the protocol
    specified does not exist.

    This is actually a factory-method design pattern, only with the factory
    method being hidden in the __new__ method. This is only syntactical sugar.
    Using this method, one can instantiate an, e.g., AsynchronProducer in the
    client code, but the created object will be the actual implementation.

    For example:
        p = AsynchronProducer(protocol='amqp', ...)
        # This actually instantiates an MQAsynchronProducer.
    """
    def __new__(cls, *args, **kwargs):
        if not 'protocol' in kwargs:
            raise ConfigurationError('protocol', 'Missing protocol specification')

        protocol = kwargs['protocol']
        if not protocol in cls.backends:
            raise ConfigurationError('protocol',
                'The backend specified (%s) does not exist'%protocol)
        return object.__new__(cls.backends[protocol], *args, **kwargs)

class CommChannel(object):
    def serialize(self, obj):
        """Create a transmittable representation of ``obj``."""
        raise NotImplementedError()

    def deserialize(self, repr_):
        """Create an object from its representation."""
        raise NotImplementedError()

class AsynchronProducer(MultiBackend, CommChannel):
    """Abstract interface of an asynchron producer. Sub-classes must implement
    asynchron message pushing in the push_message method."""
    def push_message(self, message, **kwargs):
        """Asynchron message pushing.

        This method returns None, or only control responses (ACK, Exception,
        etc.). This method should not return the result of the operations, as
        it is performed asynchronously.
        """
        raise NotImplementedError

class RPCProducer(MultiBackend, CommChannel):
    """Abstract interface of an RPC client. Sub-classes must implement remote
    procedure calls in the push_message method.

    Sub-classes should implement higher level abstraction for method calling;
    i.e. provide semantic methods that are implemented using push_message.
    """
    def push_message(self, message, **kwargs):
        """Synchron message pushing.

        This method sends a message or request to the remote entity, and
        returns the result of the operation (or an exception).

        When using an RPCProducer, the client must expect this function to hang
        up the execution while it waits for a response.

        Sub-classes must implement timouts as necessary.
        """
        raise NotImplementedError

class EventDrivenConsumer(MultiBackend, CommChannel):
    """Abstract interface of an event-driven message processor.

    Sub-classes must implement the start_consuming method, which registers a
    function as the message processor. Sub-classes must implement message
    pulling, and must call the registered function upon message arrival.

    Sub-classes may also implement the processor function itself, so they can
    act as self-contained services.
    """
    def __init__(self, processor, pargs=[], pkwargs={}, **config):
        """Create a consumer and register a message processor function.

        The processor function will be called upon message arrival, with the
        following arguments:

            - message: The content of the message
            - <backend_specific_arguments>
            - *args,
            - **kwargs: Specified upon registering the processor, these
                        are passed through to the processor function.
        """
        self.processor, self.pargs, self.pkwargs = \
            processor, pargs, pkwargs
    def _call_processor(self, data):
        return self.processor(data, *self.pargs, **self.pkwargs)
    def start_consuming(self):
        """Start consuming messages in an infinite loop."""
        raise NotImplementedError
