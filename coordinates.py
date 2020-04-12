"""
DIRECTORY:	https://github.com/howwallace/howw-stage-controls.git
PROGRAM:	coordinates.py
AUTHOR:		Harper O. W. Wallace
DATE:		9 Apr 2020

DESCRIPTION:
Used to manage a Cartesian coordinate system for stage positions. Vector
(V2) positions can be defined in polar or non-polar coordintes, as
detailed above __init__ below. Vectors can be added, subtracted, and
multiplied by scalars (note that scalar multiplication must be done as
V2 * k, not k * V2). V2 callable properties include magnitude, unit
(returns the object's unit vector, if it has one), and perpendicular
(_clk = clockwise; _cntclk = counterclockwise).
"""


import math

""" V FOR VECTOR """
class V2(object):

    def __init__(self):
        self.x = 0
        self.y = 0
    
    # arg can be type:
    #	V2 -> returns new V2 with same coordinates
    #	tuple of ints/floats:
    #	    if polar, then	arg[0] = r and arg[1] = theta (deg)
    #	    if nonpolar, then	arg[0] = x and arg[1] = y
    #	int/float -> returns a unit vector with theta (deg) = arg
    def __init__(self, arg, polar = False):
        if type(arg) is V2:
            self.x = arg.x
            self.y = arg.y
        elif type(arg) is tuple:
            if not polar:
                self.x = arg[0]
                self.y = arg[1]
            else:
                V2.__init__(self, V2(arg[1]) * arg[0])
        elif type(arg) is float or type(arg) is int:
            self.x = math.cos(math.radians(arg))
            self.y = math.sin(math.radians(arg))
        elif type(arg) is str:      # in format "(x, y)")
            x_str, y_str = arg.split(",")
            self.x = float(x_str[1:])
            self.y = float(y_str[:-1])
        else:
            self.x = 0
            self.y = 0
    
    @property
    def magnitude(self):
        return ((self.x**2 + self.y**2)**0.5)

    # returns self's unit vector
    @property
    def unit(self):
        if self.magnitude == 0:
            return V2((0, 0))
        return self / self.magnitude

    # returns a vector perpendicular to and of the same magnitude as
    # self, by clockwise rotation
    @property
    def perpendicular_clk(self):
        return V2((self.y, -self.x))

    # returns a vector perpendicular to and of the same magnitude as
    # self, by counterclockwise rotation
    @property
    def perpendicular_cntclk(self):
        return V2((-self.y, self.x))

    def asV2(self):
        return V2((self.x, self.y))

    # sets the coordinates of self to match those of pt (V2)
    def setXY(self, pt):
        self.x = pt.x
        self.y = pt.y

    def round(self):
        return V2((int(self.x), int(self.y)))

    def __add__(self, other):
        return V2((self.x + other.x, self.y + other.y))
            
    def __sub__(self, other):
        return V2((self.x - other.x, self.y - other.y))

    def __mul__(self, scalar):
        return V2((scalar * self.x, scalar * self.y))
    
    def __truediv__(self, inv_scalar):
        return V2((self.x / inv_scalar, self.y / inv_scalar))

    def __abs__(self):
        return V2((abs(self.x), abs(self.y)))

    def __str__(self):
        return "V2({0:.4f}, {1:.4f})".format(self.x, self.y)


# V3 removed
