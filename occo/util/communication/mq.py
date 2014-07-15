#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

__all__ = ['MQHandler', 'MQAsynchronProducer', 'MQRPCProducer',
           'MQEventDrivenConsumer']

import comm
import occo.util as util

PROTOCOL_ID='amqp'

class MQHandler(object):
    def __init__(self, **config):
        self.credentials = pika.PlainCredentials(config['user'],
                                                 config['password'])
        connection_parameters = pika.ConnectionParameters(
            config['host'], config['port'],
            config['virtual_host'], self.credentials)
        self.connection = pika.BlockingConnection(connection_parameters)
        self.channel = self.connection.channel()
        self.default_exchange = config.get('exchange', '')
        self.default_routing_key = config.get('routing_key', None)
    def effective_exchange(self, override=None):
        return util.coalesce(override, self.default_exchange, '')
    def effective_routing_key(self, override=None):
        return util.coalesce(
            override, self.default_routing_key,
            ValueError('publish_message: Routing key is mandatory'))

    def decalre_queue(self, queue_name, **kwargs):
        self.channel.queue_declare(routing_key, **kwargs)
    def declare_response_queue(self, **kwargs):
        response = self.channel.queue_declare(exclusive=True, **kwargs)
        return response.method.queue
    def publish_message(self, msg, routing_key=None, exchange=None, **kwargs):
        self.channel.basic_publish(
            exchange=self.effective_exchange(exchange),
            routing_key=self.effective_routing_key(routing_key),
            body=msg,
            properties=properties,
            **kwargs)

@comm.register(comm.AsynchronProducer, PROTOCOL_ID)
class MQAsynchronProducer(MQHandler, comm.AsynchronProducer):
    def __init__(self, **config):
        super(MQAsynchronProducer,self).__init__(**config)

    def push_msg(self, msg, routing_key=None, **kwargs):
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

    def on_reponse(self, ch, method, props, body):
        if self.correlation_id = props.correlation_id:
            self.response = body

    def push_msg(self, msg, routing_key, **kwargs):
        if self.correlation_id != None:
            raise RuntimeError('pika is not thread safe.')

	self.correlation_id = str(uuid.uuid4())

        rkey = self.effective_routing_key(routing_key)
        self.declare_queue(rkey)
        self.publish_message(msg, routing_key=rkey,
                             properties=pika.BasicProperties(
                                 reply_to = reply_target.callback_queue,
                                 correlation_id = reply_target.corr_id),
                             **kwargs)
	
	self.channel.basic_consume(
            on_response, no_ack=True, queue=self.callback_queue)
	while self.response is None:
	    self.connection.process_data_events()
	response = self.response
        self.__reset()
        return response

@comm.register(comm.EventDrivenConsumer, PROTOCOL_ID)
class MQEventDrivenConsumer(MQHandler, comm.EventDrivenConsumer):
    def __init__(self, **config):
        pass
