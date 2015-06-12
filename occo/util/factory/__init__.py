#
# Copyright (C) 2014 MTA SZTAKI
#

"""
Generic implementation if the design pattern `Abstract Factory`_

.. _`Abstract Factory`: http://en.wikipedia.org/wiki/Abstract_factory_pattern

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>

Generally, there will be an abstract interface class, defining what a specific
class of backends can do. For example, in case of a graphical user interface,
there may be a class called ``UI`` defining a method called ``create_button``. This interface is then implemented in several ways for several backends, e.g.
``X_UI`` and ``WindowMaker_UI``, each implementing its own ``create_button``
method. The Abstract Factory allows the dynamic creation of the right backend
based on dynamic data, and allows us to extend the application with new
backends, without touching the core code.

This implementation of the Abstract Factory uses the constructor parameter
``protocol`` to decide which backend to instantiate. It also re-defines the
built-in ``__new__`` function to completely hide the multi-backend nature from
the client code. This makes the client code shorter. It also allows us to define
a single YAML constructor for a family of classes. That is, backends can be
instantiated from configuration files, without any support from the client code.

Example classes
~~~~~~~~~~~~~~~

.. code-block:: python
    :emphasize-lines: 1,6,14,20

    import occo.util.factory as factory

    # The UI class is prepared to be an abstract factory,
    # __new__ is overridden.
    # A YAML constructor '!UI' is created.
    @factory.MultiBackend
    class UI(object):
        def __init__(protocol, **kwargs):
            do_something_with_kwargs()
        def create_button(self):
            raise NotImplementedError()

    # The class is registered as a backend for protocol='X'
    @factory.register(UI, 'X')
    class X_UI(UI):
        def create_button(self):
            x_specific_create_button()

    # The class is registered as a backend for protocol='wm'
    @factory.register(UI, 'wm')
    class WindowMaker_UI(UI)
        def create_button(self):
            windowmaker_create_button()

.. _factory_example_config:

Example configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml
    :emphasize-lines: 5,6

    app_config:
        something: nothing
    other_config:
        etc:
            ui: !UI
                protocol: X
                backend: specific
                configuration: data

"""

__all__ = ['register', 'MultiBackend']

import occo.exceptions as exc
import occo.util as util
import yaml
import logging

log = logging.getLogger('occo.util')

def split(mapping):
    if not 'protocol' in mapping:
        raise exc.ConfigurationError(
            'protocol', 'Missing protocol specification')
    protocol = mapping.pop('protocol')
    return mapping, protocol

class YAMLConstructor(object):
    def __init__(self, cls):
        self.cls = cls
    def __call__(self, loader, node):
        kwargs, protocol = split(loader.construct_mapping(node, deep=True))

        try:
            return self.cls.instantiate(protocol, **kwargs)
        except Exception as ex:
            raise exc.ConfigurationError(
                'config',
                'Abstract factory error while parsing YAML: %s'%ex,
                loader, node)

class RegisteredBackend(object):
    """ Documentation below, at ``register`` because of autodoc """
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
"""Decorator class to register backends for the abstract classes.

:param target: the target primitive, of which the decorated class is an
    implementation
:param id_:    protocol identifier; an arbitrary string that identifies the
    set of backends
"""

class MultiBackend(object):
    """
    Automates backend selection based on configuration parameters.
    """

    @classmethod
    def instantiate(cls, protocol, *args, **kwargs):
        """
        Instantiates the given class while inhibiting implicit __init__ call.
        This lets the factory __new__ hide the protocol specification from the
        factory class.

        Use this to instantiate factory classes from code.

        This method will instantiate the correct backend identified by
        ``protocol`` in ``kwargs``.

        :raises occo.exceptions.ConfigurationError: if ``protocol`` is not
            specified in ``kwargs``, or the backend identified by ``protocol``
            does not exist.
        """

        if not hasattr(cls, 'backends'):
            raise exc.ConfigurationError(
                'backends',
                "The MultiBackend class '%s' has no registered backends."%cls.__name__)
        if not protocol in cls.backends:
            raise exc.ConfigurationError('protocol',
                'The backend specified (%s) does not exist'%protocol)

        objclass = cls.backends[protocol]
        obj = object.__new__(cls.backends[protocol])
        objclass.__init__(obj, *args, **kwargs)
        return obj

    @classmethod
    def from_config(cls, cfg):
        if isinstance(cfg, basestring):
            return cls.instantiate(protocol=cfg)
        elif isinstance(cfg, dict):
            try:
                return cls.instantiate(
                    cfg['protocol'],
                    *cfg.get('args', tuple()),
                    **cfg.get('kwargs', dict()))
            except KeyError:
                raise ValueError('Invalid backend configuration', cls, cfg)
        else:
            raise ValueError('Invalid backend configuration', cls, cfg)

    @classmethod
    def has_backend(cls, protocol):
        return hasattr(cls, 'backends') \
            and protocol in cls.backends
