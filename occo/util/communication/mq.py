#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

__all__ = ['MQHandler', 'MQAsynchronProducer', 'MQRPCProducer',
           'MQEventDrivenConsumer']

import comm
import occo.util as util
import pika
import uuid
import logging

log = logging.getLogger()

PROTOCOL_ID='amqp'

class MQHandler(object):
    def __init__(self, **config):
        self.credentials = pika.PlainCredentials(config['user'],
                                                 config['password'])
        connection_parameters = pika.ConnectionParameters(
            config['host'], config.get('port', 5672),
            config['vhost'], self.credentials)
        self.connection = pika.BlockingConnection(connection_parameters)
        self.channel = self.connection.channel()
        self.queue = config.get('queue', None)
        self.default_exchange = config.get('exchange', '')
        self.default_routing_key = config.get('routing_key', None)
    def effective_exchange(self, override=None):
        return util.coalesce(override, self.default_exchange, '')
    def effective_routing_key(self, override=None):
        return util.coalesce(
            override, self.default_routing_key,
            ValueError('publish_message: Routing key is mandatory'))

    def declare_queue(self, queue_name, **kwargs):
        self.channel.queue_declare(queue_name, **kwargs)
    def declare_response_queue(self, **kwargs):
        response = self.channel.queue_declare(exclusive=True, **kwargs)
        return response.method.queue
    def publish_message(self, msg, routing_key=None, exchange=None, **kwargs):

        self.channel.basic_publish(
            exchange=self.effective_exchange(exchange),
            routing_key=self.effective_routing_key(routing_key),
            body=msg,
            **kwargs)
    def setup_consumer(self, callback, queue, **kwargs):
        self.channel.basic_consume(callback, queue=queue,
                                   **kwargs)

@comm.register(comm.AsynchronProducer, PROTOCOL_ID)
class MQAsynchronProducer(MQHandler, comm.AsynchronProducer):
    def __init__(self, **config):
        super(MQAsynchronProducer,self).__init__(**config)

    def push_message(self, msg, routing_key=None, **kwargs):
        rkey = self.effective_routing_key(routing_key)
        self.declare_queue(rkey)
        self.publish_message(msg, routing_key=rkey, **kwargs)

@comm.register(comm.RPCProducer, PROTOCOL_ID)
class MQRPCProducer(MQHandler, comm.RPCProducer):
    def __init__(self, **config):
        super(MQRPCProducer,self).__init__(**config)
        self.callback_queue = self.declare_response_queue()
        self.__reset()

    def __reset(self):
        self.response = None
        self.correlation_id = None

    def on_response(self, ch, method, props, body):
        log.debug('RPC response callback; received message: %r, expecting %r',
                  props.correlation_id, self.correlation_id)
        if self.correlation_id == props.correlation_id:
            self.response = body

    def push_message(self, msg, routing_key=None, **kwargs):
        if self.correlation_id != None:
            raise RuntimeError('pika is not thread safe.')

        self.correlation_id = str(uuid.uuid4())
        try:
            rkey = self.effective_routing_key(routing_key)
            self.declare_queue(rkey)
            self.publish_message(msg, routing_key=rkey,
                                 properties=pika.BasicProperties(
                                     reply_to = self.callback_queue,
                                     correlation_id = self.correlation_id),
                                 **kwargs)

            self.setup_consumer(self.on_response, no_ack=True,
                                queue=self.callback_queue)
            log.debug('RPC push message: waiting for response')
            while self.response is None:
                self.connection.process_data_events()
            log.debug('RPC push message: received response: %r', self.response)
            return self.response
        finally:
            self.__reset()

@comm.register(comm.EventDrivenConsumer, PROTOCOL_ID)
class MQEventDrivenConsumer(MQHandler, comm.EventDrivenConsumer):
    def __init__(self, processor, pargs=[], pkwargs={},
                 cancel_event=None, **config):
        super(MQEventDrivenConsumer, self).__init__(**config)
        comm.EventDrivenConsumer.__init__(
            self, processor=processor, pargs=pargs, pkwargs=pkwargs)
        if not self.queue:
            raise ValueError('Queue name is mandatory')
        self.cancel_event = cancel_event
        self.declare_queue(self.queue)
        self.channel.basic_qos(prefetch_count=1)
        self.setup_consumer(self.callback, queue=self.queue)

    def callback(self, ch, method, props, body):
        log.debug('Consumer: message has arrived; calling internal method')
        retval = self._call_processor(body)
        log.debug('Consumer: internal method exited')
        if props.reply_to:
            log.debug('Consumer: RPC message, responding')
            self.publish_message(str(retval),
                                 exchange='',
                                 routing_key=props.reply_to,
                                 properties=pika.BasicProperties(
                                     correlation_id=props.correlation_id))
            log.debug('Consumer: response sent')
        log.debug('Consumer: ACK-ing')
        ch.basic_ack(delivery_tag=method.delivery_tag)
        log.debug('Consumer: done')

    @property
    def cancelled(self):
        return self.cancel_event and self.cancel_event.is_set()

    def start_consuming(self):
        log.debug('Starting consuming')
        while not self.cancelled:
            self.connection.process_data_events()
        log.debug('Consumer cancelled, exiting.')
    def __call__(self):
        try:
            return self.start_consuming()
        except KeyboardInterrupt:
            log.debug('Ctrl-C Exiting.')
        except Exception:
            log.exception('Consuming:')
