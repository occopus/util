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

class MQBootstrapTest(unittest.TestCase):
    def setUp(self):
        self.test_config = dict(protocol='amqp', extra='something')
        self.fail_config = dict(extra='something')
    def test_inst(self):
        map(lambda (cls1, cls2): \
                self.assertEqual(cls1(**self.test_config).__class__, cls2),
            [(comm.AsynchronProducer, mq.MQAsynchronProducer),
             (comm.RPCProducer, mq.MQRPCProducer),
             (comm.EventDrivenConsumer, mq.MQEventDrivenConsumer)])
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
        c = comm.EventDrivenConsumer(**self.config.endpoints['consumer_rpc'])
    @unittest.skip('not finished test case')
    def test_rpc(self):
        MSG='test message abc'
        p = comm.RPCProducer(**self.config.endpoints['producer_rpc'])
        c = comm.EventDrivenConsumer(**self.config.endpoints['consumer_rpc'])
        def consumer_core(self, msg, *args, **kwargs):
            return msg
        c.start_consuming(consumer_core)
        self.assertEqual(p.push_message(MSG), MSG)
    @unittest.skip('not finished test case')
    def test_async(self):
        MSG='test message abc'
        p = comm.RPCProducer(**self.config.endpoints['producer_async'])
        c = comm.EventDrivenConsumer(**self.config.endpoints['consumer_async'])
        p.push_message(MSG)
        def consumer_core(self, msg, *args, **kwargs):
            self.assertEqual(msg, MSG)
        c.start_consuming(self.consumer_core)

class MQTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(
            self, it.chain(
                map(MQBootstrapTest, ['test_inst',
                                      'test_bad_inst']),
                map(MQConnectionTest, ['test_rpc',
                                       'test_async'])
            ))

if __name__ == '__main__':
    alltests = unittest.TestSuite([MQTestSuite(),
                                   ])
    unittest.main()
