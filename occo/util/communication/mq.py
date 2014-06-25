#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

__all__ = ['MQHandler', 'MQAsynchronProducer', 'MQRPCProducer',
           'MQEventDriverConsumer']

import occo.util.communication as com

PROTOCOL_ID='amqp'

class MQHandler(object):
    def __init__(self, **config):
        pass

@com.register(com.AsynchronProducer, PROTOCOL_ID)
class MQAsynchronProducer(MQHandler, com.AsynchronProducer):
    def __init__(self, **config):
        pass

@com.register(com.RPCProducer, PROTOCOL_ID)
class MQRPCProducer(MQHandler, com.RPCProducer):
    def __init__(self, **config):
        pass

@com.register(com.EventDrivenConsumer, PROTOCOL_ID)
class MQEventDrivenConsumer(MQHandler, com.EventDrivenConsumer):
    def __init__(self, **config):
        pass
