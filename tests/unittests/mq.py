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

class MQTestSuite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(
            self, map(MQTest, ['test_inst',
                               'test_bad_inst']))

if __name__ == '__main__':
    alltests = unittest.TestSuite([MQTestSuite(),
                                   ])
    unittest.main()
