#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

__all__ = ['AsynchronProducer', 'RPCProducer', 'EventDrivenConsumer']

class AsynchronProducer(object):
    def __init__(self):
        pass
    def push_message(self, message, **kwargs):
        raise NotImplementedError

class RPCProducer(object):
    def __init__(self):
        pass
    def push_message(self, message, **kwargs):
        raise NotImplementedError

class EventDriveConsumer(object):
    def __init__(self):
        pass
    def start_consuming(self, processor, **kwargs):
        raise NotImplementedError
