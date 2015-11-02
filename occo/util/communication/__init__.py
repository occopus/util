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

"""
Communication in OCCO is performed through abstract interfaces. Currently,
these interfaces are implemented using the AMQP protocol using ``pika``.

Three abstract interfaces are provided:
 - Asynchronous message passing

   Messages are sent asynchronously, using a given rouing key. Only
   ACKnowledgement is expected.
 - RPC calls

   The message processor is expected to return a result. Currently, there is no
   support for timeout or interruption.
 - Event-driven message processing

   A processor function must be provided by the client code. Whenever a message
   arrives, the processor function is called. If the message was an RPC
   message, the result is returned to the caller.

The abstract classes implement the *abstract factory* pattern. That is,
implementing classes should not be instantiated directly. Instantiating an
abstract class will check the ``protocol`` specified in the configuration,
and instantiates the real backend automatically.

.. warning::
    AMQP implementations require context management.

Example
-------
``config.yaml``

.. code-block:: yaml

    mqconfig:
        protocol: amqp
        host: 192.168.152.184
        vhost: test
        exhange: ''
        routing_key: test
        queue: test
        user: test
        password: test

``async_producer_example.py``

.. code-block:: python

    import occo.util.config as config
    import occo.util.communication as comm

    with open('config.yaml') as f
        cfg = config.DefaultYAMLConfig(f)

    prod = comm.AsynchronProducer(**cfg.mqconfig)
    with prod:
        prod.push_message('test message')

``rpc_producer_example.py``

.. code-block:: python

    import occo.util.config as config
    import occo.util.communication as comm

    with open('config.yaml') as f
        cfg = config.DefaultYAMLConfig(f)

    prod = comm.RPCProducer(**cfg.mqconfig)
    with prod:
        try:
            data = prod.push_message('test message')
        except comm.CommunicationError as e:
            print e
        except ApplicationError as e:
            # do application specific error handling here
        else:
            print data

``infinite_consumer_example.py``

.. code-block:: python

    import occo.util.config as config
    import occo.util.communication as comm

    with open('config.yaml') as f
        cfg = config.DefaultYAMLConfig(f)

    def core_func(msg):
        print msg
        retval = 'hello, {0}'.format(msg)
        return comm.Response(200, retval)

    cons = comm.EventDrivenConsumer(core_func, **cfg.mqconfig)
    with cons:
        cons.start_consuming()

``interruptable_consumer_example.py``

.. code-block:: python

    import occo.util.config as config
    import occo.util.communication as comm
    import threading

    with open('config.yaml') as f
        cfg = config.DefaultYAMLConfig(f)

    def core_func(msg):
        print msg
        retval = 'hello, {0}'.format(msg)
        return comm.Response(200, retval)

    cancel = threading.Event()
    cons = comm.EventDrivenConsumer(core_func,
                                    cancel_event=cancel,
                                    **cfg.mqconfig)
    t = threading.Thread(cons)
    with cons:
        t.start()
        threading.sleep(10)
        cancel.set()
        t.join()

"""

from comm import *
from mq import *
