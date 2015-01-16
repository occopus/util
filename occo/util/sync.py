#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

import threading

exiting = None

def init():
    global
    exiting = threading.Event()


