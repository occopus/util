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

CFG_FILE='comm_test_cfg.yaml'

def dummy(ch, method, *args, **kwargs):
    ch.basic_ack(delivery_tag=method.delivery_tag)

class MQBootstrapTest(unittest.TestCase):
    def setUp(self):
        with open(CFG_FILE) as cfg:
            cfg = config.DefaultYAMLConfig(cfg)
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
        with open('comm_test_cfg.yaml') as cfg:
            self.config = config.DefaultYAMLConfig(cfg)
    def test_rpc_init_prod(self):
        p = comm.RPCProducer(**self.config.endpoints['producer_rpc'])
    def test_async_init_prod(self):
        p = comm.AsynchronProducer(**self.config.endpoints['producer_async'])
    def test_init_consumer(self):
        c = comm.EventDrivenConsumer(dummy, **self.config.endpoints['consumer_rpc'])
    def test_rpc(self):
        MSG='test message abc'
        e = threading.Event()
        def consumer_core(msg, *args, **kwargs):
            return msg
        p = comm.RPCProducer(**self.config.endpoints['producer_rpc'])
        c = comm.EventDrivenConsumer(consumer_core, cancel_event=e,
                                     **self.config.endpoints['consumer_rpc'])
        t = threading.Thread(target=c)
        t.start()
        self.assertEqual(p.push_message(MSG), MSG)
        e.set()
        t.join()
    def test_async(self):
        MSG='test message abc'
        e = threading.Event()
        def consumer_core(msg, *args, **kwargs):
            self.assertEqual(msg, MSG)
            e.set()
        p = comm.AsynchronProducer(**self.config.endpoints['producer_async'])
        c = comm.EventDrivenConsumer(consumer_core, cancel_event=e,
                                     **self.config.endpoints['consumer_async'])
        t = threading.Thread(target=c)
        t.start()
        p.push_message(MSG)
        e.wait()
        t.join()

if __name__ == '__main__':
    import os
    print 'PID: %d'%os.getpid()
    unittest.main()
