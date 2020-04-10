from threading import RLock


class PortLock(object):
    """ A class used to provide separate read and write access in multithread environment.

    Provides properties readLock and writeLock returning separate RLocks to allow specific access.
    In addition provides same interface as threading.RLock. Using this interface both locks are acquired
    in defined order.
    """

    def __init__(self):
        self._read_lock = RLock()
        self._write_lock = RLock()

    def acquire(self, blocking=True):
        if blocking:
            self._read_lock.acquire()
            self._write_lock.acquire()
            return None
        else:
            if not self._read_lock.acquire(blocking=False):
                return False

            if not self._write_lock.acquire(blocking=False):
                self._read_lock.release()
                return False

            return True

    def release(self):
        self._write_lock.release()
        self._read_lock.release()

    __enter__ = acquire

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    @property
    def read_lock(self):
        return self._read_lock

    @property
    def write_lock(self):
        return self._write_lock
