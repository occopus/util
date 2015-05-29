#
# Copyright (C) 2014 MTA SZTAKI
#

"""AMQP implementation of the abstract communication interfaces

.. moduleauthor:: Adam Visegradi <adam.visegradi@sztaki.mta.hu>

This module implements the abstract interfaces specified in
:mod:`occo.util.communication.comm` using the pika_ implementation of the AMQP_
protocol.

.. _pika: https://pika.readthedocs.org/
.. _AMQP: http://www.amqp.org/
"""

__all__ = ['MQHandler', 'MQAsynchronProducer', 'MQRPCProducer',
           'MQEventDrivenConsumer']

import comm
import occo.util as util
import occo.exceptions as exc
import occo.util.factory as factory
import pika
import uuid
import logging
import threading
import yaml

log = logging.getLogger('occo.util.comm.mq')

#: These implementations are identified with the following protocol key:
PROTOCOL_ID='amqp'

class YAMLChannel(comm.CommChannel):
    """Implement channel serialization with YAML"""
    def serialize(self, obj):
        """Create a transmittable representation of ``obj``."""
        return yaml.dump(obj)

    def deserialize(self, repr_):
        """Create an object from its representation."""
        return yaml.load(repr_)

class MQHandler(object):
    """Common functions for all AMQP implementations.

    Supports and **requires context management** (:keyword:`with`). The
    connection is established only when entering a context.

    :keyword str host: Host name of the AMQP server.
    :keyword int port: Port of the AMQP server. *Optional*, the default is ``5672``.
    :keyword str vhost: Virtual host on the AMQP server to connect to.
    :keyword str user: User name.
    :keyword str password: Password.
    :keyword str exchange: Default exchange, may be overridden by client methods.
        *Optional*, the default is ``''``.
    :keyword str routing_key: Default routing key, may be overridden by client
        methods. *Optional*, the default is ``None``.
    :keyword bool auto_delete: Auto delete queue. *Optional*, the default is ``False``.

    Subclasses may require additional configuration parameters.
    """
    def __init__(self, **config):
        try:
            log.debug('Config:\n%r', config)
            self.credentials = pika.PlainCredentials(
                config['user'], config['password'])
            self.connection_parameters = pika.ConnectionParameters(
                config['host'], config.get('port', 5672),
                config['vhost'], self.credentials)
        except KeyError as e:
            raise exc.ConfigurationError(e)
        self.default_exchange = config.get('exchange', '')
        self.default_routing_key = config.get('routing_key', None)
        self.auto_delete = config.get('auto_delete', False)

    def __enter__(self):
        self.connection = pika.BlockingConnection(self.connection_parameters)
        self.channel = self.connection.channel()
        return self
    def __exit__(self, type, value, tb):
        self.channel.close()

    def effective_exchange(self, override=None):
        """Selects the exchange in effect.

        The effective value is determined based on the following order:
          1. The one specified as the argument ``override``
          2. The default exchange of this object
              (``MQHandler.__init__(exchange=...)``)
          3. Default: ``''``
        """
        return util.coalesce(override, self.default_exchange, '')

    def effective_routing_key(self, override=None):
        """Selects the routing key in effect.

        The effective value is determined based on the following order:
          1. The one specified as the argument ``override``
          2. The default routing key of this object
             (``MQHandler.__init__(routing_key=...)``)

        :raises ValueError: if no routing key is in effect. (Assuming that a
            routing key is mandatory.)
        """
        return util.coalesce(
            override, self.default_routing_key,
            ValueError('publish_message: Routing key is mandatory'))

    def declare_queue(self, queue_name, **kwargs):
        """Declares a non-exclusive queue with the given name.

        :param str queue_name: The queue to be declared.
        :param `**kwargs`: Keyword arguments are passed through to the backend.
        """
        self.channel.queue_declare(
            queue_name, auto_delete=self.auto_delete, **kwargs)
    def declare_response_queue(self, **kwargs):
        """Declares an auto-named, exclusive queue.

        :param `**kwargs`: Keyword arguments are passed through to the backend.
        """
        response = self.channel.queue_declare(exclusive=True, **kwargs)
        return response.method.queue
    def publish_message(self, msg, routing_key=None, exchange=None, **kwargs):
        """Publishes a message.

        The message will be published to the exchange determined by
        :meth:`effective_exchange`, and with a routing key determined by
        :meth:`effective_routing_key`.

        :param object msg: The object to be delivered. The message will be
            serialized for transfer.
        :param routing_key: *Optional.* The routing key of the message.
        :param exchange: *Optional.* The exchange to send the message to.
        :param `**kwargs`: Keyword arguments are passed through to the backend.
        """
        self.channel.basic_publish(
            exchange=self.effective_exchange(exchange),
            routing_key=self.effective_routing_key(routing_key),
            body=self.serialize(msg),
            **kwargs)

    def setup_consumer(self, callback, queue, **kwargs):
        """Registers a consumer callback for the given queue.

        :param callable callback: The callback function to be registered. The
            signature of this callable must match that specified in the `pika
            documentation`_.
        :param queue: The name of the queue the callback function will be
            registered with.
        :param `**kwargs`: Keyword arguments are passed through to the backend.

        .. _`pika documentation`: http://pika.readthedocs.org/en/latest/examples/blocking_consume.html
        """
        self.channel.basic_consume(callback, queue=queue, **kwargs)

@factory.register(comm.AsynchronProducer, PROTOCOL_ID)
class MQAsynchronProducer(MQHandler, comm.AsynchronProducer, YAMLChannel):
    """AMQP implementation of
    :class:`occo.util.communication.comm.AsynchronProducer` using
    :class:`MQHandler`.

    :param `**config`: Configuration for the :class:`MQHandler` backend.

    .. warning:: Use context management with this class (:keyword:`with`).
    """
    def __init__(self, **config):
        super(MQAsynchronProducer,self).__init__(**config)

    def push_message(self, msg, routing_key=None, **kwargs):
        """Push a message to the backend queue.

        :param object msg: The data to be delivered.
        :param str routing_key: *Optional.* The routing key of the message. If
            unspecified, the default routing key is used.
        :param `**kwargs`: Keyword arguments are passed through to the backend.
        """
        rkey = self.effective_routing_key(routing_key)
        self.declare_queue(rkey)
        self.publish_message(msg, routing_key=rkey, **kwargs)

@factory.register(comm.RPCProducer, PROTOCOL_ID)
class MQRPCProducer(MQHandler, comm.RPCProducer, YAMLChannel):
    """AMQP implementation of
    :class:`occo.util.communication.comm.RPCProducer` using :class:`MQHandler`.

    This class is thread safe by mut.ex. access: at any time, only one RPC call
    can be pending. For multiple, simultaneous RPC calls, use multiple
    instances of this class.

    :param `**config`: Configuration for the :class:`MQHandler` backend.

    .. warning:: Use context management with this class (:keyword:`with`).

    .. todo:: It would be desirable to factor :meth:`__reset` out (it's ugly
        and bug-prone). Two ideas: co-routines (:keyword:`yield`) and closures
        (moving the callback inside :meth:`push_message`). We should think this
        through and fix it sometime.
    """
    def __init__(self, **config):
        super(MQRPCProducer,self).__init__(**config)
        # This class requires mutex access.
        self.lock = threading.Lock()
        self.__reset()

    def __reset(self):
        """ Because the result arrives through a callback, these variables
        cannot be method-local variables: the callback function and the
        push_message function must share this data. This implies that these
        variables must be reset between calls to avoid interference.
        """
        self.response = None
        self.correlation_id = None

    def __enter__(self):
        super(MQRPCProducer, self).__enter__()
        self.callback_queue = self.declare_response_queue()
        self.setup_consumer(
            self.__on_response, no_ack=True, queue=self.callback_queue)
    def __exit__(self, type, value, tb):
        super(MQRPCProducer, self).__exit__(type, value, tb)

    def __on_response(self, ch, method, props, body):
        """Callback function for RPC response.

        It sets the value of ``self.response``
        """
        log.debug('RPC response callback; received message: %r, expecting %r',
                  props.correlation_id, self.correlation_id)
        if self.correlation_id == props.correlation_id:
            self.response = body

    def push_message(self, msg, routing_key=None, **kwargs):
        """Pushes a message and waits for response."""

        # try-finally is used instead of 'with self.lock' to avoid a level of
        # indent. But, when __reset will be factored out, this can be fixed.
        try:
            self.lock.acquire()
            self.correlation_id = str(uuid.uuid4())

            # Ensure queue exists
            rkey = self.effective_routing_key(routing_key)
            self.declare_queue(rkey)

            # Send request
            self.publish_message(msg, routing_key=rkey,
                                 properties=pika.BasicProperties(
                                     reply_to = self.callback_queue,
                                     correlation_id = self.correlation_id),
                                 **kwargs)

            # Wait for response
            log.debug('RPC push message: waiting for response')
            while self.response is None:
                self.connection.process_data_events()
            log.debug('RPC push message: received response: %r', self.response)

            # Process response
            response = self.deserialize(self.response)
            response.check()

            return response.data
        finally:
            # Must reset variables used to communicate between this function
            # and the callback. See class docstring.
            self.__reset()
            self.lock.release()

@factory.register(comm.EventDrivenConsumer, PROTOCOL_ID)
class MQEventDrivenConsumer(MQHandler, comm.EventDrivenConsumer, YAMLChannel):
    """AMQP implementation of
    :class:`occo.util.communication.comm.EventDrivenConsumer` using
    :class:`MQHandler`.

    Supports being the target of a :class:`threading.Thread`.

    :param callable processor: The core function to be called when a message
        arrives.  For details, see the documentation of
        :class:`~occo.util.communication.comm.EventDrivenConsumer`.
    :param list pargs: See
        :class:`~occo.util.communication.comm.EventDrivenConsumer`.
    :param list pkwargs:
        See :class:`~occo.util.communication.comm.EventDrivenConsumer`.
    :param threading.Event cancel_event: *Optional.* If specified, the method
        :meth:`start_consuming` will not yield, but can be aborted by signaling
        this event. If unspecified, the method will yield immediately after
        processing a batch of data events, so it can be used in a
        non-parellelized application.
    :param `**config`: Configuration
        for the :class:`MQHandler` backend.

    .. warning:: Use context management with this class (:keyword:`with`).

    .. automethod:: __call__
    """
    def __init__(self, processor, pargs=[], pkwargs={},
                 cancel_event=None, **config):
        super(MQEventDrivenConsumer, self).__init__(**config)
        comm.EventDrivenConsumer.__init__(
            self, processor=processor, pargs=pargs, pkwargs=pkwargs)
        self.cancel_event = cancel_event
        try:
            self.queue = config['queue']
        except KeyError:
            raise exc.ConfigurationError('queue', 'Queue name is mandatory')

    def __enter__(self):
        super(MQEventDrivenConsumer, self).__enter__()
        self.declare_queue(self.queue)
        self.channel.basic_qos(prefetch_count=1)
        self.setup_consumer(self.__callback, queue=self.queue)

    def __reply_if_rpc(self, response, props):
        """This method sends a response *iff* the message was an RPC message.

        :param response: The response to the query.
        :type response: :class:`~occo.util.communication.comm.Response`
        :param props: AMQP property bag of the query, possibly containing the
            ``reply_to`` queue and the ``correlation_id``.
        """
        if props.reply_to:
            log.debug('RPC message, responding')
            try:
                self.publish_message(response,
                                     exchange='',
                                     routing_key=props.reply_to,
                                     properties=pika.BasicProperties(
                                         correlation_id=props.correlation_id))
            except Exception:
                log.exception('Error sending response:')
            else:
                log.debug('Response sent')

    def __callback(self, ch, method, props, body):
        """
        Callback method for AMQP, as specified by the `pika documentation`_.

        This method processes the incoming message as specified by
        :class:`occo.util.communication.comm.EventDrivenConsumer`.
        """
        log.debug('Message has arrived; message body:\n%s', body)
        try:
            try:
                log.debug('Calling internal method')
                retval = self._call_processor(self.deserialize(body))
            except comm.CommunicationError as e:
                log.debug('Internal method signaled an error.')
                response = comm.ExceptionResponse(e.http_code, e)
            else:
                log.debug('Internal method exited')
                response = retval

            self.__reply_if_rpc(response, props)
        except Exception:
            log.exception('Unhandled exception:')
            response = comm.Response(500, 'Internal Server Error')
            self.__reply_if_rpc(response, props)
        finally:
            # ACK the message iff the processor implied that the query should
            # be finalized.
            if response is None or response.finalize:
                log.debug('Consumer: ACK-ing')
                ch.basic_ack(delivery_tag=method.delivery_tag)
            log.debug('Consumer: done')

    @property
    def cancelled(self):
        """Returns True iff :meth:`start_consuming` should yield.

        That is: if ``cancel_event`` is not specified at all, or if the
        client has signalled through it.
        """
        return not self.cancel_event or self.cancel_event.is_set()

    def start_consuming(self):
        """Process queue events until :meth:`cancelled` signals the need to
        yield."""
        while not self.cancelled:
            self.connection.process_data_events()
    def __call__(self):
        """Entry point for :meth:`threading.Thread.run()`"""
        try:
            return self.start_consuming()
        except KeyboardInterrupt:
            log.debug('Ctrl-C Exiting.')
        except Exception:
            log.exception('Consuming:')
