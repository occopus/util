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
    def __init__(self, infra_id, reason=None, *args):
        Exception.__init__(self, *args)
        self.infra_id = infra_id
        self.reason = reason

    def __reduce__(self):
        a = super(InfraProcessorError, self).__reduce__()
        return a[0], self.__getinitargs__(), a[2]

    def __getinitargs__(self):
        return (self.infra_id, self.reason) + self.args

    def __repr__(self):
        return '{classname}({infraid!r}, {reason!r}, {args})'.format(
            classname=self.__class__.__name__,
            infraid=self.infra_id,
            reason=self.reason,
            args=', '.join(repr(i) for i in self.args))

    def __str__(self):
        return repr(self)

class MinorInfraProcessorError(InfraProcessorError):
    """
    A subclass of :class:`InfraProcessorError`\ s that signals a trivial error
    that can be ignored in respect to the overall infrastructure.
    """
    pass

class CriticalInfraProcessorError(InfraProcessorError):
    """
    A subclass of :class:`InfraProcessorError`\ s that signals the suspension
    of the maintenance of the infrastructure.
    """
    pass

class NoMatchingNodeDefinition(CriticalInfraProcessorError):
    """
        Exception raised when there are no matching node definitions. Raised by
        uds.get_node_definition
    """
    def __init__(self, infra_id, filter_keywords, node_type, *args):
        super(NoMatchingNodeDefinition,
              self).__init__(infra_id, 'No matching node definition', *args)
        self.filter_keywords = filter_keywords
        self.node_type = node_type
    def __getinitargs__(self):
        return (self.infra_id,
                self.filter_keywords,
                self.node_type) + self.args

class NodeCreationError(CriticalInfraProcessorError):
    """
    Critical error happening in the process of creating a node. Upon such an
    error, the maintenance of the infrastructure must be suspended.

    :param dict instance_data: The instance data pertaining to the (partially)
        created node. If partial, it must contain at least the ``infra_id`` and
        the ``node_id`` involved.
    :param Exception reason: The original error that has happened.
    """
    def __init__(self, instance_data=None, reason=None):
        self.reason = reason
        self.instance_data = instance_data

    def __getinitargs__(self):
        return self._instance_data, self.reason

    @property
    def instance_data(self):
        return self._instance_data

    @instance_data.setter
    def instance_data(self, instance_data):
        self._instance_data = instance_data
        if instance_data:
            super(NodeCreationError, self).__init__(
                    instance_data['infra_id'],
                    self.reason,
                    'Node creation error',
                    instance_data['node_id'])
        else:
            super(NodeCreationError, self).__init__(
                    None, self.reason, 'Node creation error', None)

    def __repr__(self):
        return '{classname}(<instance_data:{nodeid}>, {reason!r})'.format(
            classname=self.__class__.__name__,
            nodeid=self.instance_data['node_id'],
            reason=self.reason)

class NodeContextSchemaError(NodeCreationError):
    """
    Error happening in the process of checking the context string syntax. Upon such an
    error, the maintenance of the infrastructure must be same as in case of
    NodeCreationError.

    :param dict instance_data: The instance data pertaining to the (partially)
        created node. If partial, it must contain at least the ``infra_id`` and
        the ``node_id`` involved.
    :param Exception reason: The original error that has happened.
    """
    def __init__(self, node_definition, reason=None, msg=None):
        super(self.__class__, self).__init__(None, reason)
        self.node_definition = node_definition
        self.msg = msg

    def __getinitargs__(self):
        return self.node_definition, self.reason, self.msg

    def __repr__(self):
        return '{classname}(<node_definition:{nodeid}>, {reason!r})'.format(
            classname=self.__class__.__name__,
            nodeid=self.node_definition['node_id'],
            reason=self.reason)

    def __str__(self):
        if self.msg:
            return self.msg
        else:
            return super(self.__class__, self).__str__()

class NodeCreationTimeOutError(NodeCreationError):
    """
    Error happening when timout is reached in the process of creating node. 
    Upon such an error, the maintenance of the infrastructure must be same as in case of
    NodeCreationError.

    :param dict instance_data: The instance data pertaining to the (partially)
        created node. If partial, it must contain at least the ``infra_id`` and
        the ``node_id`` involved.
    :param Exception reason: The original error that has happened.
    """
    def __init__(self, instance_data, reason=None, msg=None):
        super(self.__class__, self).__init__(instance_data, reason)
        self.msg = msg

    def __getinitargs__(self):
        return self._instance_data, self.reason, self.msg

    def __str__(self):
        if self.msg:
            return self.msg
        else:
            return super(self.__class__, self).__str__()

class NodeFailedError(NodeCreationError):
    """
    This exception is raised when a node becomes finalized while creating it.
    I.e., it failes, or is shut down unexpectedly.

    :param dict instance_data: The instance data pertaining to the (partially)
        created node. If partial, it must contain at least the ``infra_id`` and
        the ``node_id`` involved.
    :param str state: The final state of the node.
    """
    def __init__(self, instance_data, state):
        super(self.__class__, self).__init__(instance_data)
        self.state = state

    def __getinitargs__(self):
        return self._instance_data, self.state

    def __str__(self):
        return "Node has failed (state={0})".format(self.state)

class InfrastructureCreationError(CriticalInfraProcessorError):
    """
    Critical error happening when creating the infrastructure.
    """
    pass
