class AsciiMovementMixin(object):
    """Provides mixin giving ability to move device, axis or lockstep.
    """
    def home(self):
        """Sends the "home" command, then polls the device or axis until it is
        idle.

        Raises:
            UnexpectedReplyError: The reply received was not sent by the
                expected device or axis.

        Returns:
            An AsciiReply containing the first reply received.
        """
        reply = self.send("home")
        self.poll_until_idle()
        return reply

    def move_abs(self, position, blocking=True):
        """Sends the "move abs" command to the device or axis to move it to the
        specified position, then polls the device until it is idle.

        Args:
            position: An integer representing the position in
                microsteps to which to move the device.
            blocking: An optional boolean, True by default. If set to
                False, this function will return immediately after
                receiving a reply from the device and it will not poll
                the device further.

        Raises:
            UnexpectedReplyError: The reply received was not sent by
                the expected device or axis.

        Returns:
            An AsciiReply containing the first reply received.
        """
        reply = self.send("move abs {0:d}".format(position))
        if blocking:
            self.poll_until_idle()
        return reply

    def move_rel(self, distance, blocking=True):
        """Sends the "move rel" command to the device or axis to move it by the
        specified distance, then polls the device until it is idle.

        Args:
            distance: An integer representing the number of microsteps
                by which to move the device.
            blocking: An optional boolean, True by default. If set to
                False, this function will return immediately after
                receiving a reply from the device, and it will not poll
                the device further.

        Raises:
            UnexpectedReplyError: The reply received was not sent by
                the expected device or axis.

        Returns:
            An AsciiReply containing the first reply received.
        """
        reply = self.send("move rel {0:d}".format(distance))
        if blocking:
            self.poll_until_idle()
        return reply

    def move_vel(self, speed, blocking=False):
        """Sends the "move vel" command to make the device or axis move at the
        specified speed.

        Args:
            speed: An integer representing the speed at which to move
                the device.
            blocking: An optional boolean, False by default. If set to
                True, this function will poll the device repeatedly
                until it reports that it is idle.

        Notes:
            Unlike the other two move commands, move_vel() does not by
            default poll the device until it is idle. move_vel() will
            return immediately after receiving a response from the
            device unless the "blocking" argument is set to True.

        Raises:
            UnexpectedReplyError: The reply received was not sent by
                the expected device or axis.

        Returns:
            An AsciiReply containing the first reply received.
        """
        reply = self.send("move vel {0:d}".format(speed))
        if blocking:
            self.poll_until_idle()
        return reply

    def stop(self):
        """Sends the "stop" command to the device or axis.

        Notes:
            The stop command can be used to pre-empt any movement
            command in order to stop the device early.

        Raises:
            UnexpectedReplyError: The reply received was not sent by
                the expected device or axis.

        Returns:
            An AsciiReply containing the first reply received.
        """
        reply = self.send("stop")
        self.poll_until_idle()
        return reply
