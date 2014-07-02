#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

__all__ = ['MQHandler', 'MQAsynchronProducer', 'MQRPCProducer',
           'MQEventDrivenConsumer']

import comm

PROTOCOL_ID='amqp'

class MQHandler(object):
    def __init__(self, **config):
        pass

@comm.register(comm.AsynchronProducer, PROTOCOL_ID)
class MQAsynchronProducer(MQHandler, comm.AsynchronProducer):
    def __init__(self, **config):
        self.host = config['host']

@comm.register(comm.RPCProducer, PROTOCOL_ID)
class MQRPCProducer(MQHandler, comm.RPCProducer):
    def __init__(self, **config):

        self.credentials = pika.PlainCredentials(config['user'],config['password'])
        self.connectionParameters = pika.ConnectionParameters(config['host'],config['port'],
config['virtual_host'],self.credentials)
        self.connection = pika.BlockingConnection(connectionParameters)
        self.channel =self.connection.channel()

	returnValue = self.channel.queue_declare(exclusive=True)
	self.callback_queue = returnValue.method.queue

	self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)


    def on_response(self, ch, method, props, body):
	if self.corr_id == props.correlation_id:
	    self.response = body


    def push_msg(self, msg, **kwargs):

	self.response = None
	self.corr_id =uuid.uuid4())

#TODO: routing key is permanent, solution needed (routing key will be part of msg)
	self.channel.basic_publish(exchange='', routing_key='rpc_queue',
properties=pika.BasicProperties(reply_to = self.callback_queue, correlation_id = self.corr_id), body = msg)
	
	while self.response is None:
	    self.connection.process_data_events()
	return self.response

	pass

@comm.register(comm.EventDrivenConsumer, PROTOCOL_ID)
class MQEventDrivenConsumer(MQHandler, comm.EventDrivenConsumer):
    def __init__(self, **config):
        pass
