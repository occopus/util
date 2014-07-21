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
        self.fail_config_2 = dict(protocol='amqp', processor=None)
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
    def test_bad_amqp(self):
        def tst(cls):
            with self.assertRaises(comm.ConfigurationError):
                cls(**self.fail_config_2)
        map(tst, [comm.AsynchronProducer, comm.RPCProducer,
                  comm.EventDrivenConsumer])

class MQConnectionTest(unittest.TestCase):
    def setUp(self):
        self.data = None
    def test_rpc_init_prod(self):
        with comm.RPCProducer(**cfg.endpoints['producer_rpc']):
            pass
    def test_async_init_prod(self):
        with comm.AsynchronProducer(**cfg.endpoints['producer_async']):
            pass
    def test_init_consumer(self):
        with comm.EventDrivenConsumer(dummy, **cfg.endpoints['consumer_rpc']):
            pass
    def i_test_rpc(self):
        MSG='test message abc'
        EXPECTED='RE: test message abc'
        e = threading.Event()
        def consumer_core(msg, *args, **kwargs):
            log.debug('RPC Consumer: message has arrived')
            return 'RE: %s'%msg
        p = comm.RPCProducer(**cfg.endpoints['producer_rpc'])
        c = comm.EventDrivenConsumer(consumer_core, cancel_event=e,
                                     **cfg.endpoints['consumer_rpc'])
        with p, c:
            log.debug('RPC Creating thread object')
            t = threading.Thread(target=c)
            log.debug('RPC Starting thread')
            t.start()
            log.debug('RPC thread started, sending RPC message and '
                      'waiting for response')
            retval = p.push_message(MSG)
            log.debug('Response arrived')
            self.assertEqual(retval, EXPECTED)
            log.debug('Setting cancel event')
            e.set()
            log.debug('Waiting for RPC Consumer to exit')
            t.join()
            log.debug('Consumer exited')
    def test_rpc(self):
        log.debug('Starting test RPC')
        try:
            self.i_test_rpc()
        except Exception:
            log.exception('RPC test failed:')

    def i_test_rpc_double(self):
        MSG, MSG2 = 'test message abc', 'hello'
        EXPECTED, EXPECTED2 = 'RE: test message abc', 'RE: hello'
        e = threading.Event()
        def consumer_core(msg, *args, **kwargs):
            log.debug('Double RPC Consumer: message has arrived')
            return 'RE: %s'%msg
        p = comm.RPCProducer(**cfg.endpoints['producer_rpc'])
        c = comm.EventDrivenConsumer(consumer_core, cancel_event=e,
                                     **cfg.endpoints['consumer_rpc'])
        with c:
            log.debug('Double RPC Creating thread object')
            t = threading.Thread(target=c)
            log.debug('Double RPC Starting thread')
            t.start()
            log.debug('Double RPC thread started, sending RPC message and '
                      'waiting for response')
            with p:
                retval = p.push_message(MSG)
            log.debug('Sending second RPC message and waiting for response')
            with p:
                retval2 = p.push_message(MSG2)
            log.debug('Second response arrived')
            self.assertEqual(retval, EXPECTED)
            self.assertEqual(retval2, EXPECTED2)
            log.debug('Setting cancel event')
            e.set()
            log.debug('Waiting for RPC Consumer to exit')
            t.join()
            log.debug('Consumer exited')
    def test_rpc_double(self):
        log.debug('Starting double test RPC')
        try:
            self.i_test_rpc_double()
        except Exception:
            log.exception('Double RPC test failed:')

    def test_async(self):
        MSG = 'test message abc'
        EXPECTED = 'RE: test message abc'
        e = threading.Event()
        r = threading.Event()
        def consumer_core(msg, *args, **kwargs):
            log.debug('Async Consumer: message has arrived')
            self.data = 'RE: %s'%msg
            log.debug('Async Consumer: setting response event')
            r.set()
            log.debug('Async consumer: response event has been set')
        p = comm.AsynchronProducer(**cfg.endpoints['producer_async'])
        c = comm.EventDrivenConsumer(consumer_core, cancel_event=e,
                                     **cfg.endpoints['consumer_async'])
        with p, c:
            log.debug('Async Creating thread object')
            t = threading.Thread(target=c)
            log.debug('Async Starting thread')
            t.start()
            log.debug('Async thread started, sending Async message')
            p.push_message(MSG)
            log.debug('Waiting Async arrival')
            r.wait()
            log.debug('Async message has arrived')
            self.assertEqual(self.data, EXPECTED)
            log.debug('Setting Async cancel event')
            e.set()
            log.debug('Waiting for Async Consumer to exit')
            t.join()
            log.debug('Consumer exited')

if __name__ == '__main__':
    import os
    log.info('PID: %d', os.getpid())
    try:
        unittest.main()
    except KeyboardInterrupt:
        log.debug('Ctrl-C Exiting.')
    finally:
        logging.shutdown()
