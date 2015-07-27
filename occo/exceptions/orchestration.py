#
# Copyright (C) 2014 MTA SZTAKI
#

"""This module contains OCCO exceptions for orchestration events.

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>
"""

class InfraProcessorError(Exception):
    """
    Exception raised when performing InfraProcessor command objects.
    """
    pass

class CriticalInfraProcessorError(InfraProcessorError):
    """
    A subclass of :class:`InfraProcessorError`\ s that signal the suspension of
    the maintenance of the infrastructure.

    :param str infra_id: The identifier of the affected infrastructure.
    :param * args: Arguments for the :class:`Exception` class.
    """
    def __init__(self, infra_id, *args):
        Exception.__init__(self, *args)
        self.infra_id = infra_id

class NoMatchingNodeDefiniton(CriticalInfraProcessorError):
    """
        Exception raised when there are no matching node definitions. Raised by
        uds.get_node_definition
    """
    def __init__(self, infra_id, preselected_backend_ids, node_type, *args):
        super(NoMatchingNodeDefinition,
              self).__init__(infra_id, 'No matching node definition', *args)
        self.preselected_backend_ids = preselected_backend_ids
        self.node_type = node_type

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
                                                'Node creation error',
                                                instance_data['node_id'])
        self.instance_data = instance_data
        self.reason = reason
