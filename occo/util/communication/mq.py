#
# Copyright (C) 2014 MTA SZTAKI
#
# AMQP communication for the SZTAKI Cloud Orchestrator
#

"""AMQP implementation of the abstract communication interfaces

This module implements the abstract interfaces specified in
occo.util.communication using the pika AMQP implementation.
"""

__all__ = ['MQHandler', 'MQAsynchronProducer', 'MQRPCProducer',
           'MQEventDrivenConsumer']

import comm
import occo.util as util
import occo.util.factory as factory
import pika
import uuid
import logging
import threading
import yaml

log = logging.getLogger('occo.util.comm.mq')

# These implementations are identified with the following protocol key:
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

    Supports and requires context management. The connection is established
    only when entering a context.
    """
    def __init__(self, **config):
        """Initializes the AMQP object based on a dictionary configuration.

        The configuration of the connection must be specified as keyword
        arguments, including the following elements

        host:
          Host name of the AMQP server.
        port:
          Port of the AMQP server.
          *Optional*, the default is ``5672``.
        vhost:
          Virtual host on the AMQP server to connect to.
        user, password:
          Authentication data
        exchange:
          Default exchange, may be overridden by client methods.
          *Optional*, the default is ``''``.
        routing_key:
          Default routing_key, may be overridden by client methods.
          *Optional*, the default is ``None``.

        Subclasses may require additional configuration parameters.
        """
        try:
            log.debug('Config:\n%r', config)
            self.credentials = pika.PlainCredentials(
                config['user'], config['password'])
            self.connection_parameters = pika.ConnectionParameters(
                config['host'], config.get('port', 5672),
                config['vhost'], self.credentials)
        except KeyError as e:
            raise util.ConfigurationError(e)
        self.default_exchange = config.get('exchange', '')
        self.default_routing_key = config.get('routing_key', None)

    def __enter__(self):
        self.connection = pika.BlockingConnection(self.connection_parameters)
        self.channel = self.connection.channel()
        return self
    def __exit__(self, type, value, tb):
        self.channel.close()

    def effective_exchange(self, override=None):
        """Selects the exchange in effect.

        The effective value is determined based on the following order:
          1. The one specified as an argument
          2. The default exchange of this object
          3. ``''``
        """
        return util.coalesce(override, self.default_exchange, '')
    def effective_routing_key(self, override=None):
        """Selects the routing key in effect.

        The effective value is determined based on the following order:
          1. The one specified as an argument
          2. The default routing key of this object

        Assumed that a routing key is mandatory, this method raises
        ``ValueError`` if no routing key is in effect.
        """
        return util.coalesce(
            override, self.default_routing_key,
            ValueError('publish_message: Routing key is mandatory'))

    def declare_queue(self, queue_name, **kwargs):
        """Declares a non-exclusive queue with the given name."""
        self.channel.queue_declare(queue_name, **kwargs)
    def declare_response_queue(self, **kwargs):
        """Declares an auto-named, exclusive queue."""
        response = self.channel.queue_declare(exclusive=True, **kwargs)
        return response.method.queue
    def publish_message(self, msg, routing_key=None, exchange=None, **kwargs):
        """Publishes a message.

        The message will be published to the exchange specified by
        :func:`effective_exchange`, and with a routing key specified by
        :func:`effective_routing_key`.

        The message will be serialized for transfer.

        ``kwargs`` are passed to ``basic_publish``.
        """
        self.channel.basic_publish(
            exchange=self.effective_exchange(exchange),
            routing_key=self.effective_routing_key(routing_key),
            body=self.serialize(msg),
            **kwargs)
    def setup_consumer(self, callback, queue, **kwargs):
        """Registers a consumer callback for the given queue.

        ``kwargs`` are passed to ``basic_consume``.
        """
        self.channel.basic_consume(callback, queue=queue, **kwargs)

@factory.register(comm.AsynchronProducer, PROTOCOL_ID)
class MQAsynchronProducer(MQHandler, comm.AsynchronProducer, YAMLChannel):
    """AMQP implementation of
    :class:`occo.util.communication.comm.AsynchronProducer`

    .. warning::

        Use context management with this class.
    """
    def __init__(self, **config):
        super(MQAsynchronProducer,self).__init__(**config)

    def push_message(self, msg, routing_key=None, **kwargs):
        rkey = self.effective_routing_key(routing_key)
        self.declare_queue(rkey)
        self.publish_message(msg, routing_key=rkey, **kwargs)

@factory.register(comm.RPCProducer, PROTOCOL_ID)
class MQRPCProducer(MQHandler, comm.RPCProducer, YAMLChannel):
    """AMQP implementation of
    :class:`occo.util.communication.comm.RPCProducer`

    This class is thread safe through mutex access: at any time, only one
    RPC call can be pending.

    For multiple, simultaneous RPC calls, use multiple instances of this class.

    .. warning::

        Use context management with this class.
    """
    def __init__(self, **config):
        super(MQRPCProducer,self).__init__(**config)
        # This class requires mutex access.
        self.lock = threading.Lock()
        self.__reset()

    def __reset(self):
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
        """Callback function for RPC response."""
        log.debug('RPC response callback; received message: %r, expecting %r',
                  props.correlation_id, self.correlation_id)
        if self.correlation_id == props.correlation_id:
            self.response = body

    def push_message(self, msg, routing_key=None, **kwargs):
        """Pushes a message and waits for response."""

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

            response = self.deserialize(self.response)
            response.check()

            return response.data
        finally:
            self.__reset()
            self.lock.release()

@factory.register(comm.EventDrivenConsumer, PROTOCOL_ID)
class MQEventDrivenConsumer(MQHandler, comm.EventDrivenConsumer, YAMLChannel):
    """AMQP implementation of
    :class:`occo.util.communication.comm.EventDrivenConsumer`

    Supports being the target of a threading.Thread.

    .. warning::

        Use context management with this class.
    """
    def __init__(self,
                 processor, pargs=[], pkwargs={},
                 cancel_event=None,
                 **config):
        super(MQEventDrivenConsumer, self).__init__(**config)
        comm.EventDrivenConsumer.__init__(
            self, processor=processor, pargs=pargs, pkwargs=pkwargs)
        self.cancel_event = cancel_event
        try:
            self.queue = config['queue']
        except KeyError:
            raise util.ConfigurationError('queue', 'Queue name is mandatory')

    def __enter__(self):
        super(MQEventDrivenConsumer, self).__enter__()
        self.declare_queue(self.queue)
        self.channel.basic_qos(prefetch_count=1)
        self.setup_consumer(self.__callback, queue=self.queue)

    def __reply_if_rpc(self, response, props):
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
            if response.finalize:
                log.debug('Consumer: ACK-ing')
                ch.basic_ack(delivery_tag=method.delivery_tag)
            log.debug('Consumer: done')

    @property
    def cancelled(self):
        """Returns true iff consuming has been cancelled; based on
        ``cancel_event``."""
        return self.cancel_event and self.cancel_event.is_set()

    def start_consuming(self):
        """Starts processing queue until cancelled."""
        log.debug('Starting consuming')
        while not self.cancelled:
            self.connection.process_data_events()
        log.debug('Consumer cancelled, exiting.')
    def __call__(self):
        """Entry point for ```threading.Thread.run()```"""
        try:
            return self.start_consuming()
        except KeyboardInterrupt:
            log.debug('Ctrl-C Exiting.')
        except Exception:
            log.exception('Consuming:')
