#
# Copyright (C) 2014 MTA SZTAKI
#

"""
Primitives for parallel processing.
"""

__all__ = ['exiting', 'GracefulProcess', 'init']

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

import multiprocessing

class StillRunning(Exception): pass

class GracefulProcess(multiprocessing.Process):
    """
    Extends :class:`multiprocessing.Process` with graceful exiting.

    Processes of this kind are terminated in the following manner:

        - First, SIGINT is used. The process should catch it as a
          :exc:`KeyboardInterrupt`, and handle it gracefully.

        - If the process is still running after a specified timeout,
          it is sent the SIGTERM signal. The process will probably terminate
          normally, but without executing cleanup code (``finally``, etc.)

        - If the process is still running after another timeout period, it
          is probably unable to terminate on its own. In this case, the process
          is killed with SIGKILL.

    """

    SIGLIST = ['SIGINT', 'SIGTERM', 'SIGKILL']

    def graceful_terminate(self, timeout):
        from itertools import izip

        for sig, next_sig in izip(self.SIGLIST, self.SIGLIST[1:]):
            try:
                self._trykill(sig, timeout)
            except StillRunning:
                log.warning('%s: Process %d has not exited in %d seconds. '
                            'Trying %s...', sig, self.pid, timeout, nextsig)
                continue
            else:
                break

    def _trykill(self, signame, timeout):
        import os, signal
        sig = getattr(signal, signame)
        os.signal(sig, self.pid)

        try:
            p.join(timeout)
        except BaseException:
            log.exception('')

        if self.is_alive():
            raise StillRunning()
