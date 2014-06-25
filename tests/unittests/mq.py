#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

import unittest
from common import *
import occo.util.communication as comm
import occo.util.communication.mq as mq

class MQTest(unittest.TestCase):
    def setUp(self):
        self.test_config = dict(protocol='amqp', extra='something')
        self.fail_config = dict(extra='something')
    def test_inst(self):
        self.assertEqual(
            comm.AsynchronProducer(**self.test_config).__class__,
            mq.MQAsynchronProducer)
        self.assertEqual(
            comm.RPCProducer(**self.test_config).__class__,
            mq.MQRPCProducer)
        self.assertEqual(
            comm.EventDrivenConsumer(**self.test_config).__class__,
            mq.MQEventDrivenConsumer)

class MQTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(
            self, map(MQTest, ['test_inst',
                               ]))

if __name__ == '__main__':
    alltests = unittest.TestSuite([MQTestSuite(),
                                   ])
    unittest.main()
