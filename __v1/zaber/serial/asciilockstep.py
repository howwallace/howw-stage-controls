from .asciilockstepinfo import AsciiLockstepInfo
from .asciimovementmixin import AsciiMovementMixin
from .utils import isstring


class AsciiLockstep(AsciiMovementMixin):
    """Represents an lockstep group of particular device (AsciiDevice).
    Allows to setup and control lockstep (synchronized movement of axes).

    Attributes:
        device: The AsciiDevice of this lockstep group.
        lockstep_group: The lockstep group number of the device. 1-9.

    .. lockstep section: http://www.zaber.com/wiki/Manuals/ASCII_
        Protocol_Manual#lockstep
    """

    def __init__(self, device, lockstep_group=1):
        """Constructs object allowing to setup lockstep (synchronized movement of axes).
        Controls movement of the lockstep.
        Requires instance of AsciiDevice on which lockstep is performed.

        Args:
            device: An AsciiDevice instance on which lockstep is performed.
            lockstep_group: An integer representing the lockstep group of this
                device. It must be between 1-9.
                Different devices may suport different number of lockstep group.
                Defaults to lockstep group 1.

        Raises:
            ValueError: The lockstep_group was not between 1 and 9.

        .. lockstep section: http://www.zaber.com/wiki/Manuals/ASCII_
            Protocol_Manual#lockstep
        """
        AsciiMovementMixin.__init__(self)

        if lockstep_group < 1 or lockstep_group > 9:
            raise ValueError("lockstep_group must be between 1 and 9.")

        self.device = device
        self.lockstep_group = lockstep_group

    def disable(self):
        """Disables this lockstep group. Allows participating axes to move independently again.

        Returns:
            An AsciiReply containing the reply received.
        """
        reply = self.send("setup disable")
        return reply

    def enable(self, axis1=1, axis2=2):
        """Enables this lockstep group and sets up axes participating in lockstep group.
        After calling this function axes will move together maintaining offset from
        time of this call.

        Future movement must be performed using this lockstep group (this instance).
        Movement commands sent directly to axis or device won't be performed.

        Args:
            axis1: An integer between 1 and 9 representing the first device axis
                which participates in lockstep group. Defaults to first axis of the device.
            axis2: An integer between 1 and 9 representing the second device axis
                which participates in lockstep group. Defaults to second axis of the device.

        Returns:
            An AsciiReply containing the reply received.

        .. lockstep section: http://www.zaber.com/wiki/Manuals/ASCII_
            Protocol_Manual#lockstep
        """
        reply = self.send("setup enable {} {}".format(axis1, axis2))
        return reply

    def info(self):
        """Queries lockstep group's state returning AsciiLockstepInfo.
        Observe AsciiLockstepInfo.is_enabled to determine whether lockstep is enabled for this lockstep group.
        Observe AsciiLockstepInfo.twist to find out whether axis are in perfect sync.

        Returns:
            An AsciiLockstepInfo containing the state of this lockstep group.
        """
        reply = self.send("info")
        return AsciiLockstepInfo(reply.data)

    def poll_until_idle(self):
        """Polls the lockstep group's status, blocking until it is idle.

        Returns:
            An AsciiReply containing the last reply received.
        """
        info = self.info()
        # it is sufficient to poll just one axis
        return self.device.poll_until_idle(axis_number=info.axis1)

    def get_status(self):
        """Queries the lockstep for its status and returns the result.

        Returns:
            A string containing either "BUSY" or "IDLE", depending on
            the response received from the device.
        """
        info = self.info()
        # it is sufficient to query just one axis
        return self.device.get_status(axis_number=info.axis1)

    def send(self, message):
        """Sends a raw message to this lockstep group, then waits for a reply.
        It is preferred to use functions as e.g. "enable" or "move_abs" to perform commands
        rather than sending raw messages using this function.

        Args:
            message: A string representing the message
                to be sent to the lockstep group.

        Raises:
            UnexpectedReplyError: The reply received was not sent by
                the expected device.
            TypeError: The message is not a string.

        Returns:
            An AsciiReply containing the reply received.
        """
        if not isstring(message):
            raise TypeError("message must be a string.")

        return self.device.send("lockstep {} {}".format(self.lockstep_group, message))
