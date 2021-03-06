import logging
import time

from .asciiaxis import AsciiAxis
from .asciicommand import AsciiCommand
from .unexpectedreplyerror import UnexpectedReplyError
from .asciimovementmixin import AsciiMovementMixin
from .asciilockstep import AsciiLockstep

# See https://docs.python.org/2/howto/logging.html#configuring-logging-
# for-a-library for info on why we have these two lines here.
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class AsciiDevice(AsciiMovementMixin):
    """Represents an ASCII device. It is safe to use in multi-threaded
    environments.

    Attributes:
        port: The port to which this device is connected.
        address: The address of this device. 1-99.
    """

    def __init__(self, port, address):
        """
        Args:
            port: An AsciiSerial object representing the port to which
                this device is connected.
            address: An integer representing the address of this
                device. It must be between 1-99.

        Raises:
            ValueError: The address was not between 1 and 99.
        """
        AsciiMovementMixin.__init__(self)

        if address < 1 or address > 99:
            raise ValueError("Address must be between 1 and 99.")
        self.address = address
        self.port = port

    def axis(self, number):
        """Returns an AsciiAxis with this device as a parent and the
        number specified.

        Args:
            number: The number of the axis. 1-9.

        Notes:
            This function will always return a *new* AsciiAxis instance.
            If you are working extensively with axes, you may want to
            create just one set of AsciiAxis objects by directly using
            the AsciiAxis constructor instead of this function to avoid
            creating lots and lots of objects.

        Returns:
            A new AsciiAxis instance to represent the axis specified.
        """
        return AsciiAxis(self, number)

    def lockstep(self, lockstep_group=1):
        """Returns an AsciiLockstep using this device for lockstep (synchronized movement of axes).

        Args:
            lockstep_group: The number of the lockstep group between 1-9.
                Defaults to first lockstep group of the device.

        Notes:
            This function will always return a *new* AsciiLockstep instance.
            If you are working extensively with locksteps, you may want to
            preserve returned instance instead of calling the function repeatedly.

        Returns:
            A new AsciiLockstep instance to represent the lockstep group specified.
        """
        return AsciiLockstep(self, lockstep_group=lockstep_group)

    def send(self, message):
        r"""Sends a message to the device, then waits for a reply.

        Args:
            message: A string or AsciiCommand representing the message
                to be sent to the device.

        Notes:
            Regardless of the device address specified in the message,
            this function will always send the message to this device.
            The axis number will be preserved.

            This behaviour is intended to prevent the user from
            accidentally sending a message to all devices instead of
            just one. For example, if ``device1`` is an AsciiDevice
            with an address of 1, device1.send("home") will send the
            ASCII string "/1 0 home\\r\\n", instead of sending the
            command "globally" with "/0 0 home\\r\\n".

        Raises:
            UnexpectedReplyError: The reply received was not sent by
                the expected device.

        Returns:
            An AsciiReply containing the reply received.
        """
        if isinstance(message, (str, bytes)):
            message = AsciiCommand(message)

        # Always send an AsciiCommand to *this* device.
        message.device_address = self.address

        with self.port.lock:
            # Write and read to the port while holding the lock
            # to ensure we get the correct response.
            self.port.write(message)
            reply = self.port.read()

        if (reply.device_address != self.address or
                reply.axis_number != message.axis_number or
                reply.message_id != message.message_id):
            raise UnexpectedReplyError(
                "Received an unexpected reply from device with address {0:d}, "
                "axis {1:d}".format(reply.device_address, reply.axis_number),
                reply
            )
        return reply

    def poll_until_idle(self, axis_number=0):
        """Polls the device's status, blocking until it is idle.

        Args:
            axis_number: An optional integer specifying a particular
                axis whose status to poll. axis_number must be between
                0 and 9. If provided, the device will only report the
                busy status of the axis specified. When omitted, the
                device will report itself as busy if any axis is moving.

        Raises:
            UnexpectedReplyError: The reply received was not sent by
                the expected device.

        Returns:
            An AsciiReply containing the last reply received.
        """
        while True:
            reply = self.send(AsciiCommand(self.address, axis_number, ""))
            if reply.device_status == "IDLE":
                break
            time.sleep(0.05)
        return reply

    def get_status(self, axis_number=0):
        """Queries the device for its status and returns the result.

        Args:
            axis_number: An optional integer specifying a particular
                axis whose status to query. axis_number must be between
                0 and 9. If provided, the device will only report the
                busy status of the axis specified. When omitted, the
                device will report itself as busy if any axis is moving.

        Raises:
            UnexpectedReplyError: The reply received was not sent by
                the expected device.

        Returns:
            A string containing either "BUSY" or "IDLE", depending on
            the response received from the device.
        """
        reply = self.send(AsciiCommand(self.address, axis_number, ""))
        return reply.device_status

    def get_position(self):
        """Queries the axis for its position and returns the result.

        Raises:
            UnexpectedReplyError: The reply received was not sent by the
                expected device and axis.

        Returns:
            A number representing the current device position in its native
            units of measure. See the device manual for unit conversions.
            If this command is used on a multi-axis device, the return value
            is the position of the first axis.
        """
        data = self.send("get pos").data
        if " " in data:
            data = data.split(" ")[0]

        return int(data)
