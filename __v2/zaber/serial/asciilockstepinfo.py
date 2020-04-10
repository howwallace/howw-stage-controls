import re

from .utils import isstring


class AsciiLockstepInfo(object):
    """Models lockstep info message reply in Zaber's ASCII protocol.

    Attributes:
        is_enabled: A boolean determining whether lockstep is enabled for this lockstep group.
        axis1: An integer between 1 and 9 representing the first axis
            for which the lockstep is enabled.
        axis2: An integer between 1 and 9 representing the second axis
            for which the lockstep is enabled.
        offset: An integer representing the offset between axis1 and axis2 for which the
            lockstep was enabled. This offset will be maintained during movement of the lockstep group.
            Offset is determined from position of both axes at time when lockstep is enabled.
        twist: An integer representing the current twist between axis1 and axis2
            considering the offset. Value 0 represents perfect sync between both axes in the lockstep group.

    .. lockstep section: http://www.zaber.com/wiki/Manuals/ASCII_
        Protocol_Manual#lockstep
    """
    def __init__(self, message_data):
        """
        Args:
            message_data: A string from AsciiReply's attribute data. It will be parsed by
                this constructor in order to populate the attributes of
                the new AsciiLockstepInfo.

        Raises:
            TypeError: The message_data is not a string.
            ValueError: The message_data string could not be parsed.

        .. _Ascii Protocol Manual: http://www.zaber.com/wiki/Manuals/AS
            CII_Protocol_Manual#lockstep
        """

        if not isstring(message_data):
            raise TypeError("message_data must be a string")

        if message_data == "disabled":
            self.is_enabled = False
            return

        self.is_enabled = True

        match = re.match(r"(\d+)\s(\d+)\s(-?\d+)\s(-?\d+)", message_data)
        if not match:
            raise ValueError("Failed to parse message_data: {}".format(message_data))

        self.axis1 = int(match.group(1))
        self.axis2 = int(match.group(2))
        self.offset = int(match.group(3))
        self.twist = int(match.group(4))

    def __str__(self):
        """Returns a string representation of AsciiLockstepInfo
        containing all attributes or string "Disabled" if lockstep is not enabled.
        """
        if not self.is_enabled:
            return "Disabled"
        return "Axis1={},Axis2={},Offset={},Twist={}".format(self.axis1, self.axis2, self.offset, self.twist)
