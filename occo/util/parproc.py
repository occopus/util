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
Primitives for parallel processing.
"""

__all__ = ['exiting', 'GracefulProcess', 'init']

import threading
import logging
import signal, os

log = logging.getLogger('occo.util.parproc')

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

        log.info('Killing process %d', self.pid)

        for sig, next_sig in izip(self.SIGLIST, self.SIGLIST[1:]):
            try:
                log.debug('Trying %s', sig)
                self._trykill(sig, timeout)
            except StillRunning:
                log.warning('%s: Process %d has not exited in %d seconds. '
                            'Trying %s...', sig, self.pid, timeout, next_sig)
                continue
            else:
                log.info('Process %d has been sucessfully killed with %s',
                         self.pid, sig)
                break

    def _trykill(self, signame, timeout):
        sig = getattr(signal, signame)
        os.kill(self.pid, sig)

        try:
            log.debug('Joining with process %d with timeout %d',
                      self.pid, timeout)
            self.join(timeout)
            log.debug('Joined process %d', self.pid)
        except BaseException:
            log.exception('')

        if self.is_alive():
            log.debug('Process %d is still alive', self.pid)
            raise StillRunning()
