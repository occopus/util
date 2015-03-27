#
# Copyright (C) 2014 MTA SZTAKI
#

"""
Primitives for global synchronization.
"""

import threading

exiting = threading.Event()
"""
Globally available :class:`~threading.Event` object that can be used to signal
threads that the application is exiting.
"""

def init():
    """
    Initialize the synchronization framework.

    Currently does nothing, is here for future-proofing.
    """
    pass
