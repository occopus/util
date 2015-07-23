#
# Copyright (C) 2014 MTA SZTAKI
#

"""This module contains OCCO exceptions for orchestration events.

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>
"""

class InfraProcessorError(Exception):
    """
    Exception raised when performing InfraProcessor command objects.

    :param str infra_id: The identifier of the affected infrastructure.
    :param Exception reason: The original error that has happened.
    :param * args: Arguments for the :class:`Exception` class.
    :param ** kwargs: Additional data, which will be stored in the object's
        ``__dict__`` attribute.
    """
    def __init__(self, infra_id, reason=None, *args, **kwargs):
        Exception.__init__(self, *args)
        self.__dict__.update(**kwargs)
        self.infra_id = infra_id
        self.reason = reason

    def __repr__(self):
        return '{classname}({infraid!r}, {reason}, {args})'.format(
            classname=self.__class__.__name__,
            infraid=self.infra_id,
            reason=self.reason,
            args=', '.join(repr(i) for i in self.args))

    def __str__(self):
        return repr(self)

class CriticalInfraProcessorError(InfraProcessorError):
    """
    A subclass of :class:`InfraProcessorError`\ s that signals the suspension
    of the maintenance of the infrastructure.
    """
    pass

class NodeCreationError(CriticalInfraProcessorError):
    """
    Critical error happening in the process of creating a node. Upon such an
    error, the maintenance of the infrastructure must be suspended.

    :param dict instance_data: The instance data pertaining to the (partially)
        created node. If partial, it must contain at least the ``infra_id`` and
        the ``node_id`` involved.
    :param Exception reason: The original error that has happened.
    """
    def __init__(self, instance_data, reason=None):
        super(NodeCreationError, self).__init__(instance_data['infra_id'],
                                                reason,
                                                'Node creation error',
                                                instance_data['node_id'])
        self.instance_data = instance_data

    def __repr__(self):
        return 'NodeCreationError({0!r}, {1!r})'.format(self.instance_data,
                                                        self.reason)

class InfrastructureCreationError(CriticalInfraProcessorError):
    """
    Critical error happening when creating the infrastructure.
    """
    pass
