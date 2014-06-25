#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

__all__ = ['MQHandler', 'MQAsynchronProducer', 'MQRPCProducer',
           'MQEventDriverConsumer']

import occo.util.communication as com

class MQHandler(object):
    def __init__(self, **config):
        pass

class MQAsynchronProducer(MQHandler, com.AsynchronProducer):
    def __init__(self, **config):
        pass

class MQRPCProducer(MQHandler, com.RPCProducer):
    def __init__(self, **config):
        pass

class MQEventDrivenConsumer(MQHandler, com.EventDrivenConsumer):
    def __init__(self, **config):
        pass
