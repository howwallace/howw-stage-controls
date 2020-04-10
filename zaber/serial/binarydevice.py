"""
DIRECTORY:	https://github.com/howwallace/howw-stage-controls.git/zaber/serial/
PROGRAM:	binarydevice.py
AUTHOR:		Zaber Technologies, Inc.
MODIFIED:	Harper O. W. Wallace
DATE:		9 Apr 2020

DESCRIPTION:
Object used to represent Zaber stages for sending commands.
"""


import time
import logging
import uuid

from random import randint
from .binarycommand import BinaryCommand
from .unexpectedreplyerror import UnexpectedReplyError

# See https://docs.python.org/2/howto/logging.html#configuring-logging-
# for-a-library for info on why we have these two lines here.
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class BinaryDevice(object):
    """A class to represent a Zaber device in the Binary protocol. It is safe
    to use in multi-threaded environments.

    Attributes:
        port: A BinarySerial object which represents the port to which
            this device is connected.
        number: The integer number of this device. 1-255.
    """
    
    def __init__(self, port, number):
        """
        Args:
            port: A BinarySerial object to use as a parent port.
            number: An integer between 1 and 255 which is the number of
                this device.

        Raises:
            ValueError: The device number was invalid.
        """
        if number > 255 or number < 1:
            raise ValueError("Device number must be 1-255.")
        self.number = number
        self.port = port
        
    def send(self, *args, await_reply = False):
        """Sends a command to this device, then waits for a response.

        Args:
            *args: Either a single BinaryCommand, or 1-3 integers
                specifying, in order, the command number, data value,
                and message ID of the command to be sent.

        Notes:
            The ability to pass integers to this function is provided
            as a convenience to the programmer. Calling
            ``device.send(2)`` is equivalent to calling
            ``device.send(BinaryCommand(device.number, 2))``.

            Note that in the Binary protocol, devices will only reply
            once they have completed a command. Since this function
            waits for a reply from the device, this function may block
            for a long time while it waits for a response. For the same
            reason, it is important to set the timeout of this device's
            parent port to a value sufficiently high that any command
            sent will be completed within the timeout.

            Regardless of the device address specified to this function,
            the device number of the transmitted command will be
            overwritten with the number of this device.

            If the command has a message ID set, this function will return
            a reply with a message ID, after checking whether the message
            IDs match.

        Raises:
            UnexpectedReplyError: The reply read was not sent by this
                device or the message ID of the reply (if in use) did not
                match the message ID of the command.

        Returns: A BinaryReply containing the reply received.
        """
        
        if len(args) == 1 and isinstance(args[0], BinaryCommand):
            command = args[0]
        elif len(args) < 4:
            command = BinaryCommand(self.number, *args)  # pylint: disable=E1120

        """
        # I don't think it's necessary to prevent replies being received in the wrong order (e.g., by checking message_id) because a device responds "busy" (cmd 255, data 255) if an additional command is given before the present one is completed.
        command.message_id = self.command_index
        self.command_index += 1
        """
        
        with self.port.lock:
            if await_reply:
                self.enable_auto_reply()
                self.port.write(command)
                return self.port.read_device(self.number)
            else:
                if await_reply is not None:
                    self.disable_auto_reply()
                self.port.write(command)
                return None

        """
        if ((reply.device_number != self.number) or
            (reply.message_id or 0) != (command.message_id or 0)):

            print("%d != %d" % (reply.device_number, self.number))
            print("OR:  %d != %d" % ((reply.message_id or 0), (command.message_id or 0)))
            raise UnexpectedReplyError(
                "Received an unexpected reply from"
                "device number %d:\n%s" %(reply.device_number, reply)
                )
        """
        #return reply


    def home(self, await_reply = False):
        return self.send(1, await_reply = await_reply)

    def move_abs(self, position, await_reply = False):
        return self.send(20, position, await_reply = await_reply)

    def move_rel(self, distance, await_reply = False):
        return self.send(21, distance, await_reply = await_reply)

    def move_vel(self, speed, await_reply = False):
        """
        Notes:
            Unlike the other "move" commands, the device replies
            immediately to this command. This means that when this
            function returns, it is likely that the device is still
            moving.
        """
        return self.send(22, speed, await_reply = await_reply)

    def stop(self):
        return self.send(23, await_reply = True)

    def set_home_speed(self, speed, await_reply = False):
        return self.send(41, speed, await_reply = await_reply)

    def set_target_speed(self, speed, await_reply = False):
        return self.send(42, speed, await_reply = await_reply)

    def set_acceleration(self, accel, await_reply = False):
        return self.send(43, accel, await_reply = await_reply)

    def set_min_position(self, position, await_reply = False):
        return self.send(106, position, await_reply = await_reply)
    
    def set_max_position(self, position, await_reply = False):
        return self.send(44, position, await_reply = await_reply)

    """
    bit:    "1" equals:     "1" means:
    0       1               disable auto-reply
    1       2               /reserved
    2       4               /reserved
    3       8               disable knob
    4       16              enable move tracking
    5       32              disable manual move tracking
    6       64              enable message IDs
    7       128             home status
    8       256             disable auto-home
    9       512             reverse knob
    10      1024            /reserved
    11      2048            /reserved
    12      4096            set home switch logic (device has active high home sensor)
    13      8192            /reserved
    14      16384           /reserved
    15      32768           /reserved
    """
    def get_device_mode(self):
        """
        default device mode for linear stages: 0
        """
        return self.get_setting(40)
    
    def set_device_mode(self, mode, await_reply = False):
        return self.send(40, mode, await_reply = await_reply)

    def enable_auto_reply(self):
        if self.number is 1:  # rotary stage
            self.port.write(BinaryCommand(self.number, 101, 0))
        else:
            self.port.write(BinaryCommand(self.number, 40, 0))
        
    def disable_auto_reply(self):
        if self.number is 1:  # rotary stage
            self.port.write(BinaryCommand(self.number, 101, 1))
        else:
            self.port.write(BinaryCommand(self.number, 40, 1))

    """
    # to make more complete: https://www.zaber.com/wiki/Manuals/Binary_Protocol_Manual#Quick_Command_Reference
    """
    
    def get_setting(self, setting_number):
        return self.send(53, setting_number, await_reply = True)#.data

    def get_status(self):
        return self.send(54, await_reply = True).data

    def get_position(self):
        return self.send(60, await_reply = True).data

    def disable_manual_move_tracking(self):
        return self.port.write(BinaryCommand(self.number, 116, 1))
