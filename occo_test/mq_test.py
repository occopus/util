### Copyright 2014, MTA SZTAKI, www.sztaki.hu
###
### Licensed under the Apache License, Version 2.0 (the "License");
### you may not use this file except in compliance with the License.
### You may obtain a copy of the License at
###
###    http://www.apache.org/licenses/LICENSE-2.0
###
### Unless required by applicable law or agreed to in writing, software
### distributed under the License is distributed on an "AS IS" BASIS,
### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
### See the License for the specific language governing permissions and
### limitations under the License.

import unittest
import occo.util as util
import occo.exceptions as exc
import occo.util.communication as comm
import occo.util.communication.mq as mq
import occo.util.config as config
import itertools as it
import threading
import logging
import logging.config
import uuid
import time

cfg = config.DefaultYAMLConfig(util.rel_to_file('comm_test_cfg.yaml'))

logging.config.dictConfig(cfg.logging)

log = logging.getLogger()

def dummy(*args, **kwargs):
    pass

class MQBootstrapTest(unittest.TestCase):
    def setUp(self):
        self.test_config = cfg.default_mqconfig
        self.fail_config_2 = dict(protocol='amqp', processor=None)
    def test_inst(self):
        list(map(lambda cls1_cls2: \
                self.assertEqual(
                    cls1_cls2[0].instantiate(**self.test_config).__class__,
                    cls1_cls2[1]),
            [(comm.AsynchronProducer, mq.MQAsynchronProducer),
             (comm.RPCProducer, mq.MQRPCProducer)]))
    def test_inst_consumer(self):
        self.assertEqual(
            comm.EventDrivenConsumer.instantiate(
                processor=dummy, **self.test_config).__class__,
            mq.MQEventDrivenConsumer)
    def test_bad_amqp(self):
        def tst(cls):
            with self.assertRaises(exc.ConfigurationError):
                cls.instantiate(**self.fail_config_2)
        list(map(tst, [comm.AsynchronProducer, comm.RPCProducer,
                  comm.EventDrivenConsumer]))

class MQConnectionTest(unittest.TestCase):
    def setUp(self):
        self.data = None
    def test_rpc_init_prod(self):
        with comm.RPCProducer.instantiate(**cfg.endpoints['producer_rpc']):
            log.debug('Test connection producer_rpc')
    def test_async_init_prod(self):
        with comm.AsynchronProducer.instantiate(
                **cfg.endpoints['producer_async']):
            log.debug('Test connection producer_async')
    def test_init_consumer(self):
        with comm.EventDrivenConsumer.instantiate(
                processor=dummy, **cfg.endpoints['consumer_rpc']):
            log.debug('Test connection consumer_rpc')
    def i_test_rpc(self):
        MSG = str(uuid.uuid4())
        EXPECTED = 'RE: {0}'.format(MSG)
        e = threading.Event()
        def consumer_core(msg, *args, **kwargs):
            log.debug('RPC Consumer: message has arrived')
            return comm.Response(200, 'RE: {0}'.format(msg))
        p = comm.RPCProducer.instantiate(**cfg.endpoints['producer_rpc'])
        c = comm.EventDrivenConsumer.instantiate(
            processor=consumer_core, cancel_event=e,
            **cfg.endpoints['consumer_rpc'])
        with p, c:
            log.debug('RPC Creating thread object')
            t = threading.Thread(target=c)
            log.debug('RPC Starting thread')
            t.start()
            log.debug('RPC thread started, sending RPC message and '
                      'waiting for response')
            try:
                retval = p.push_message(MSG)
                log.debug('Response arrived')
                self.assertEqual(retval, EXPECTED)
            finally:
                log.debug('Setting cancel event')
                e.set()
                log.debug('Waiting for RPC Consumer to exit')
                t.join()
                log.debug('Consumer exited')
    def test_rpc(self):
        log.debug('Starting test RPC')
        self.i_test_rpc()

    def test_rpc_error(self):
        MSG = str(uuid.uuid4())
        EXPECTED = 'RE: {0}'.format(MSG)
        e = threading.Event()
        def consumer_core(msg, *args, **kwargs):
            log.debug('RPC Consumer: message has arrived')
            return comm.Response(400, 'RE: {0}'.format(msg))
        p = comm.RPCProducer.instantiate(**cfg.endpoints['producer_rpc'])
        c = comm.EventDrivenConsumer.instantiate(
            processor=consumer_core, cancel_event=e,
            **cfg.endpoints['consumer_rpc'])
        with p, c:
            log.debug('RPC Creating thread object')
            t = threading.Thread(target=c)
            log.debug('RPC Starting thread')
            t.start()
            log.debug('RPC thread started, sending RPC message and '
                      'waiting for response')
            with self.assertRaises(exc.CriticalError):
                try:
                    retval = p.push_message(MSG)
                finally:
                    log.debug('Setting cancel event')
                    e.set()
                    log.debug('Waiting for RPC Consumer to exit')
                    t.join()
                    log.debug('Consumer exited')

    def test_rpc_500_exception(self):
        MSG = str(uuid.uuid4())
        EXPECTED = 'RE: {0}'.format(MSG)
        e = threading.Event()
        def consumer_core(msg, *args, **kwargs):
            log.debug('RPC Consumer: message has arrived')
            raise ValueError('Test exception')
        p = comm.RPCProducer.instantiate(**cfg.endpoints['producer_rpc'])
        c = comm.EventDrivenConsumer.instantiate(
            processor=consumer_core, cancel_event=e,
            **cfg.endpoints['consumer_rpc'])
        with p, c:
            log.debug('RPC Creating thread object')
            t = threading.Thread(target=c)
            log.debug('RPC Starting thread')
            t.start()
            log.debug('RPC thread started, sending RPC message and '
                      'waiting for response')
            with self.assertRaises(exc.TransientError):
                try:
                    retval = p.push_message(MSG)
                finally:
                    log.debug('Setting cancel event')
                    e.set()
                    log.debug('Waiting for RPC Consumer to exit')
                    t.join()
                    log.debug('Consumer exited')

    def test_rpc_comm_exception(self):
        MSG = str(uuid.uuid4())
        EXPECTED = 'RE: {0}'.format(MSG)
        e = threading.Event()
        def consumer_core(msg, *args, **kwargs):
            log.debug('RPC Consumer: message has arrived')
            return comm.ExceptionResponse(403, ValueError())
        p = comm.RPCProducer.instantiate(**cfg.endpoints['producer_rpc'])
        c = comm.EventDrivenConsumer.instantiate(
            processor=consumer_core, cancel_event=e,
            **cfg.endpoints['consumer_rpc'])
        with p, c:
            log.debug('RPC Creating thread object')
            t = threading.Thread(target=c)
            log.debug('RPC Starting thread')
            t.start()
            log.debug('RPC thread started, sending RPC message and '
                      'waiting for response')
            with self.assertRaises(ValueError):
                try:
                    retval = p.push_message(MSG)
                finally:
                    log.debug('Setting cancel event')
                    e.set()
                    log.debug('Waiting for RPC Consumer to exit')
                    t.join()
                    log.debug('Consumer exited')

    def i_test_rpc_double(self):
        salt = str(uuid.uuid4())
        MSG, MSG2 = salt, 'hello-{0}'.format(salt)
        EXPECTED, EXPECTED2 = 'RE: {0}'.format(MSG), 'RE: {0}'.format(MSG2)
        e = threading.Event()
        def consumer_core(msg, *args, **kwargs):
            log.debug('Double RPC Consumer: message has arrived')
            return comm.Response(200, 'RE: {0}'.format(msg))
        p = comm.RPCProducer.instantiate(**cfg.endpoints['producer_rpc'])
        c = comm.EventDrivenConsumer.instantiate(
            processor=consumer_core, cancel_event=e,
            **cfg.endpoints['consumer_rpc'])
        with p, c:
            log.debug('Double RPC Creating thread object')
            t = threading.Thread(target=c)
            log.debug('Double RPC Starting thread')
            t.start()
            log.debug('Double RPC thread started, sending RPC message and '
                      'waiting for response')
            try:
                retval = p.push_message(MSG)
                log.debug('Sending second RPC message and waiting for response')
                retval2 = p.push_message(MSG2)
                log.debug('Second response arrived')
                self.assertEqual(retval, EXPECTED)
                self.assertEqual(retval2, EXPECTED2)
            finally:
                log.debug('Setting cancel event')
                e.set()
                log.debug('Waiting for RPC Consumer to exit')
                t.join()
                log.debug('Consumer exited')
    def test_rpc_double(self):
        log.debug('Starting double test RPC')
        self.i_test_rpc_double()

    def test_async(self):
        MSG = 'test message abc'
        EXPECTED = 'RE: test message abc'
        e = threading.Event()
        r = threading.Event()
        def consumer_core(msg, *args, **kwargs):
            log.debug('Async Consumer: message has arrived')
            self.data = 'RE: {0}'.format(msg)
            log.debug('Async Consumer: setting response event')
            r.set()
            log.debug('Async consumer: response event has been set')
        p = comm.AsynchronProducer.instantiate(
            **cfg.endpoints['producer_async'])
        c = comm.EventDrivenConsumer.instantiate(
            processor=consumer_core, cancel_event=e,
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

def setup_module():
    import os
    log.info('PID: {0}'.format(os.getpid()))
