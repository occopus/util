#
# Copyright (C) 2014 MTA SZTAKI
#
# Communication primitives for the SZTAKI Cloud Orchestrator
#

"""
"""

__all__ = ['register', 'MultiBackend']

import occo.util as util
import yaml
import logging

log = logging.getLogger('occo.util')

class YAMLConstructor(object):
    def __init__(self, cls):
        self.cls = cls
    def __call__(self, loader, node):
        return self.cls() if type(node) is yaml.ScalarNode \
                else self.cls(**loader.construct_mapping(node, deep=True))

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
            target = self.target
            target.backends = dict()
            constructor_name = '!{0}'.format(target.__name__)
            log.debug("Adding YAML constructor for '%s' as '%s'",
                      target.__name__, constructor_name)
            yaml.add_constructor(constructor_name, YAMLConstructor(target))

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
            raise util.ConfigurationError('protocol', 'Missing protocol specification')

        protocol = kwargs['protocol']
        if not protocol in cls.backends:
            raise util.ConfigurationError('protocol',
                'The backend specified (%s) does not exist'%protocol)
        return object.__new__(cls.backends[protocol], *args, **kwargs)
