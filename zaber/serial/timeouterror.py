"""
DIRECTORY:	https://github.com/howwallace/howw-stage-controls.git/zaber/serial/
PROGRAM:	timeouterror.py
AUTHOR:		Zaber Technologies, Inc.
DATE:		9 Apr 2020

DESCRIPTION:
Error raised when the device takes too long to reply.
"""


class TimeoutError(Exception):
    """Raised when a read operation exceeded its specified time limit."""
    pass
