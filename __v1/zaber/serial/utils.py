import sys

IS_PYTHON3_PLUS = sys.version_info[0] >= 3


def isstring(anything):
    if IS_PYTHON3_PLUS:
        return isinstance(anything, str)
    else:
        return isinstance(anything, basestring)
