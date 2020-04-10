
import math

""" V FOR VECTOR """
class V2(object):

    def __init__(self):
        V2.__init__(self, 0, 0)
    
    # arg can be of type V, P, or float-tuple (degree-measure of point on unit-circle)
    """
    non-polar:  arg[0] = x;  arg[1] = y
    polar:      arg[0] = r;  arg[1] = theta (deg)
    """
    def __init__(self, arg, polar = False):
        if type(arg) is V2:
            V2.__init__(self, arg.x, arg.y)
        elif type(arg) is tuple:
            if not polar:
                self.x = arg[0]
                self.y = arg[1]
            else:
                V2.__init__(self, arg[0] * V2(arg[1]))
        elif type(arg) is float:
            V2.__init__(self, math.cos(math.radians(arg)), math.sin(math.radians(arg)))
        elif type(arg) is str:   # NEW
            x_str, y_str = arg.split(",")
            self.x = float(x_str[1:])
            self.y = float(y_str[:-1])
        else:
            V2.__init__(self)
    
    @property
    def magnitude(self):
        return ((self.x**2 + self.y**2)**0.5)

    """ x-component of unit vector """
    @property
    def unit_x(self):
        if self.magnitude == 0:
            return 0
        return self.x / self.magnitude

    """ y-component of unit vector """
    @property
    def unit_y(self):
        if self.magnitude == 0:
            return 0
        return self.y / self.magnitude

    def round(self):
        return V2((int(self.x), int(self.y)))



    def asV2(self):
        return V2((self.x, self.y))

    def setXY(self, pt):
        self.x = pt.x
        self.y = pt.y

    def __add__(self, other):
        return V2((self.x + other.x, self.y + other.y))
            
    def __sub__(self, other):
        return V2((self.x - other.x, self.y - other.y))

    def __mul__(self, scalar):
        return V2((scalar * self.x, scalar * self.y))
        
    def __div__(self, inv_scalar):
        return V2((self.x / inv_scalar, self.y / inv_scalar))

    def __str__(self):
        return "V2({0}, {1})".format(self.x, self.y)


""" 3D Vector """
class V3(V2):
    
    def __init__(self):
        V2.__init__(self)
        self.z = None
    
    # val can be of type V, P, or float (degree-measure of point on unit-circle)
    """
    non-polar:  args[0] = x;  args[1] = y
    polar:      args[0] = r;  args[1] = theta (deg)
    """
    
    def __init__(self, arg, polar = False):
        if type(arg) is V2:
            V2.__init__(self, arg.x, arg.y)
            self.z = None
        elif type(arg) is tuple:
            if not polar:
                self.x = arg[0]
                self.y = arg[1]
            else:
                V2.__init__(self, arg[0] * V(arg[1]))

            if len(arg) == 3:
                self.z = arg[2]
            else:
                self.z = None
        elif type(arg) is float:
            V2.__init__(self, math.cos(math.radians(arg)), math.sin(math.radians(arg)))
            self.z = None
        else:
            V2.__init__(self)
            
    """
        make the point represent a gap, which means it must have a negative y-coordinate
        def cast_to_gap(self):
        self.y = -math.fabs(self.y)
        """
    
    def __add__(self, other):
        return V3((self.x + other.x,
                   self.y + other.y,
                   None if (self.z is None or other.z is None) else self.z + other.z))
    
    def __str__(self):
        return "V3(" + self.x + ", " + self.y + ", " + self.z + ")"

