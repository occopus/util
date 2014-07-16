#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

import unittest
from common import *
import occo.util.communication as comm
import occo.util.communication.mq as mq
import occo.util.config as config
import itertools as it
import threading
import logging
import logging.config

CFG_FILE='comm_test_cfg.yaml'
with open(CFG_FILE) as cfg:
    cfg = config.DefaultYAMLConfig(cfg)

logging.config.dictConfig(cfg.logging)

log = logging.getLogger()

def dummy(*args, **kwargs):
    pass

class MQBootstrapTest(unittest.TestCase):
    def setUp(self):
        self.test_config = cfg.default_mqconfig
        self.fail_config = dict(extra='something')
    def test_inst(self):
        map(lambda (cls1, cls2): \
                self.assertEqual(cls1(**self.test_config).__class__, cls2),
            [(comm.AsynchronProducer, mq.MQAsynchronProducer),
             (comm.RPCProducer, mq.MQRPCProducer)])
    def test_inst_consumer(self):
        self.assertEqual(
            comm.EventDrivenConsumer(
                dummy, **self.test_config).__class__,
            mq.MQEventDrivenConsumer)
    def test_bad_inst(self):
        def tst(cls):
            with self.assertRaises(comm.ConfigurationError):
                cls(**self.fail_config)
        map(tst, [comm.AsynchronProducer, comm.RPCProducer,
                  comm.EventDrivenConsumer])

class MQConnectionTest(unittest.TestCase):
    def setUp(self):
        self.data = None
    def test_rpc_init_prod(self):
        p = comm.RPCProducer(**cfg.endpoints['producer_rpc'])
    def test_async_init_prod(self):
        p = comm.AsynchronProducer(**cfg.endpoints['producer_async'])
    def test_init_consumer(self):
        c = comm.EventDrivenConsumer(dummy, **cfg.endpoints['consumer_rpc'])
    def test_rpc(self):
        MSG='test message abc'
        e = threading.Event()
        def consumer_core(msg, *args, **kwargs):
            return msg
        p = comm.RPCProducer(**cfg.endpoints['producer_rpc'])
        c = comm.EventDrivenConsumer(consumer_core, cancel_event=e,
                                     **cfg.endpoints['consumer_rpc'])
        t = threading.Thread(target=c)
        t.start()
        log.debug('sendingrpc message')
        retval = p.push_message(MSG)
        e.set()
        t.join()
        self.assertEqual(retval, MSG)
        log.debug('sent, received rpc')
    def test_async(self):
        MSG='test message abc'
        e = threading.Event()
        def consumer_core(msg, *args, **kwargs):
            log.debug('Async Consumer: message has arrived')
            self.data = msg
            log.debug('Async Consumer: setting cancel event')
            e.set()
            log.debug('Async consumer: cancel event has been set')
        p = comm.AsynchronProducer(**cfg.endpoints['producer_async'])
        c = comm.EventDrivenConsumer(consumer_core, cancel_event=e,
                                     **cfg.endpoints['consumer_async'])
        t = threading.Thread(target=c)
        t.start()
        log.debug('Sending Async message')
        p.push_message(MSG)
        log.debug('Waiting Async arrival')
        e.wait()
        log.debug('Async message has arrived')
        self.assertEqual(self.data, MSG)
        log.debug('Waiting for Async Consumer to exit')
        t.join()

if __name__ == '__main__':
    import os
    log.info('PID: %d', os.getpid())
    unittest.main()
