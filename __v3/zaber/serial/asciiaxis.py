import logging

from .asciicommand import AsciiCommand
from .asciimovementmixin import AsciiMovementMixin
from .unexpectedreplyerror import UnexpectedReplyError

# See https://docs.python.org/2/howto/logging.html#configuring-logging-
# for-a-library for info on why we have these two lines here.
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class AsciiAxis(AsciiMovementMixin):
    """Represents one axis of an ASCII device. It is safe to use in multi-
    threaded environments.

    Attributes:
        parent: An AsciiDevice which represents the device which has
            this axis.
        number: The number of this axis. 1-9.
    """

    def __init__(self, device, number):
        """
        Args:
            device: An AsciiDevice which is the parent of this axis.
            number: The number of this axis. Must be 1-9.

        Raises:
            ValueError: The axis number was not between 1 and 9.
        """
        AsciiMovementMixin.__init__(self)

        if number < 1 or number > 9:
            raise ValueError("Axis number must be between 1 and 9.")
        self.number = number
        self.parent = device

    def send(self, message):
        """Sends a message to the axis and then waits for a reply.

        Args:
            message: A string or AsciiCommand object containing a
                command to be sent to this axis.

        Notes:
            Regardless of the device address or axis number supplied in
            (or omitted from) the message passed to this function, this
            function will always send the command to only this axis.

            Though this is intended to make sending commands to a
            particular axis easier by allowing the user to pass in a
            "global command" (ie. one whose target device and axis are
            both 0), this can result in some unexpected behaviour. For
            example, if the user tries to call send() with an
            AsciiCommand which has a different target axis number than
            the number of this axis, they may be surprised to find that
            the command was sent to this axis rather than the one
            originally specified in the AsciiCommand.

        Examples:
            Since send() will automatically set (or overwrite) the
            target axis and device address of the message, all of the
            following calls to send() will result in identical ASCII
            messages being sent to the serial port::

                >>> axis.send("home")
                >>> axis.send(AsciiCommand("home"))
                >>> axis.send("0 0 home")
                >>> axis.send("4 8 home")
                >>> axis.send(AsciiCommand(1, 4, "home"))

        Raises:
            UnexpectedReplyError: The reply received was not sent by the
                expected device and axis.

        Returns: An AsciiReply object containing the reply received.
        """
        if isinstance(message, (str, bytes)):
            message = AsciiCommand(message)

        # Always send the AsciiCommand to *this* axis.
        message.axis_number = self.number

        reply = self.parent.send(message)
        if reply.axis_number != self.number:
            raise UnexpectedReplyError(
                "Received a reply from an unexpected axis: axis {}".format(
                    reply.axis_number
                ),
                reply
            )
        return reply

    def get_status(self):
        """Queries the axis for its status and returns the result.

        Raises:
            UnexpectedReplyError: The reply received was not sent by the
                expected device and axis.

        Returns:
            A string containing either "BUSY" or "IDLE", depending on
            the response received from the axis.
        """
        return self.send("").device_status

    def get_position(self):
        """Queries the axis for its position and returns the result.

        Raises:
            UnexpectedReplyError: The reply received was not sent by the
                expected device and axis.

        Returns:
            A number representing the current device position in its native
            units of measure. See the device manual for unit conversions.
        """
        return int(self.send("get pos").data)

    def poll_until_idle(self):
        """Polls the axis and blocks until the device reports that the
        axis is idle.

        Raises:
            UnexpectedReplyError: The reply received was not sent by the
                expected device and axis.

        Returns: An AsciiReply object containing the last reply
            received.
        """
        return self.parent.poll_until_idle(self.number)
