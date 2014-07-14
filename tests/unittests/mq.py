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
    def test_rpc(self):
        pass
    def test_async(self):
        pass

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
