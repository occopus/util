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
    def publish_message(self, message,
                        routing_key=None, exchange=None, **kwargs):
        self.channel.basic_publish(
            exchange=self.effective_exchange(exchange),
            routing_key=self.effective_routing_key(routing_key),
            body=message, **kwargs)

@comm.register(comm.AsynchronProducer, PROTOCOL_ID)
class MQAsynchronProducer(MQHandler, comm.AsynchronProducer):
    def __init__(self, **config):
        super(MQAsynchronProducer,self).__init__(**config)

    def push_msg(self, msg, routing_key, **kwargs):
#TODO: better solution needed for queue_declare(wrong position)
        self.channel.queue_declare(routing_key)

        self.channel.basic_publish(exchange='', routing_key=routing_key,body=msg)

@comm.register(comm.RPCProducer, PROTOCOL_ID)
class MQRPCProducer(MQHandler, comm.RPCProducer):
    def __init__(self, **config):

        super(MQRPCProducer,self).__init__(**config)

	returnValue = self.channel.queue_declare(exclusive=True)
	self.callback_queue = returnValue.method.queue

	self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)


    def on_response(self, ch, method, props, body):
	if self.corr_id == props.correlation_id:
	    self.response = body


    def push_msg(self, msg, routing_key, **kwargs):

	self.response = None
	self.corr_id =uuid.uuid4())

#TODO: better solution needed for queue_declare (wrong position)
        self.channel.queue_declare(routing_key)

	self.channel.basic_publish(exchange='', routing_key=routing_key,
properties=pika.BasicProperties(reply_to = self.callback_queue, correlation_id = self.corr_id), body = msg)
	
	while self.response is None:
	    self.connection.process_data_events()
	return self.response

	pass

@comm.register(comm.EventDrivenConsumer, PROTOCOL_ID)
class MQEventDrivenConsumer(MQHandler, comm.EventDrivenConsumer):
    def __init__(self, **config):
        pass
