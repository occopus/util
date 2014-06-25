#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

__all__ = ['AsynchronProducer', 'RPCProducer', 'EventDrivenConsumer',
           'register', 'ConfigurationError']

class ConfigurationError(Exception):
    pass

class RegisteredBackend(object):
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
    def __new__(cls, *args, **kwargs):
        if not 'protocol' in kwargs:
            raise ConfigurationError('Missing protocol specification')

        protocol = kwargs['protocol']
        if not protocol in cls.backends:
            raise ConfigurationError(
                'The backend specified (%s) does not exist'%protocol)
        return object.__new__(cls.backends[protocol], *args, **kwargs)

class AsynchronProducer(MultiBackend):
    def push_message(self, message, **kwargs):
        raise NotImplementedError

class RPCProducer(MultiBackend):
    def push_message(self, message, **kwargs):
        raise NotImplementedError

class EventDrivenConsumer(MultiBackend):
    def start_consuming(self, processor, **kwargs):
        raise NotImplementedError
