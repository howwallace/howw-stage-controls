"""
DIRECTORY:	https://github.com/howwallace/howw-stage-controls.git/zaber/serial/
PROGRAM:	utils.py
AUTHOR:		Zaber Technologies, Inc.
DATE:		9 Apr 2020

DESCRIPTION:
Python-version dependencies.
"""


import sys

IS_PYTHON3_PLUS = sys.version_info[0] >= 3


def isstring(anything):
    if IS_PYTHON3_PLUS:
        return isinstance(anything, str)
    else:
        return isinstance(anything, basestring)
