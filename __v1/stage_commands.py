
# REFERENCE: https://www.zaber.com/support/docs/api/core-python/0.9/binary.html#binary-module

from zaber.serial import BinarySerial, BinaryDevice


# CENTER SQUARE
# BOTTOM LEFT
O_X = 35.940
O_Y = 29.300
# TOP RIGHT
TR_X = 23.887
TR_Y = 16.591

WIDTH = O_X - TR_X
HEIGHT = O_Y - TR_Y

# minor adjustments of writing region to prevent overlap without redefining global origin
REGION_O_X = -1.0
REGION_O_Y = 0.6



def main():

    define_operating_constants()
    
    setup_stages()

    #rotary.move_abs(mm2rotdata(143.6))
    rotary.move_abs(1)
    

def setup_stages():

    global rotary, xAxis, yAxis
    
    serial_conn = BinarySerial(STAGES_PORT, timeout = None)

    rotary = BinaryDevice(serial_conn, 1)
    xAxis = BinaryDevice(serial_conn, 2)
    yAxis = BinaryDevice(serial_conn, 3)
    
    xAxis.set_home_speed(mm2lindata(DEFAULT_HOMING_SPEED))
    xAxis.set_home_speed(mm2lindata(DEFAULT_HOMING_SPEED))

    rotary.set_acceleration(20)
    xAxis.set_acceleration(2000)
    yAxis.set_acceleration(2000)

    # rotary.set_max_position
    
    home_all()


def move_to(x = None, y = None, z = None):
   return None 

def home_all():
    rotary.home(await_reply = False)
    xAxis.home(await_reply = False)
    yAxis.home(await_reply = False)


# converts distance in mm to distance in linear stage data
# returns an integer
def mm2lindata(mm):
    return (int)(mm / MM_PER_MSTEP)

# converts distance in mm to degree-related rotary stage data
# returns an integer
def mm2rotdata(mm):
    if (mm < 140.3535 or mm > 152.808):
        print("TRYING TO SET LASER HEIGHT OUTSIDE SAFE RANGE...  WILL HOME Z AXIS INSTEAD")
        return 0
    M_EMPIR = -9.2597       # (deg/mm) empirical conversion
    B_EMPIR = 1414.9692     # (deg) empirical conversion
    return (int)((M_EMPIR * mm + B_EMPIR))# * DATA_PER_DEG)


def define_operating_constants():
    
    """         ZABER CONTROL         """

    global STAGES_PORT, DEFAULT_HOMING_SPEED, MM_PER_MSTEP, DATA_PER_DEG, MSTEP_VEL_PER_MM_VEL, DELTA_T, WIDE_GAP, LASER_HOME_HEIGHT, LASER_MIN_HEIGHT, ROTARY_MIN_ANGLE, ROTARY_MAX_ANGLE, INVERT

    STAGES_PORT = "COM3"                # serial port to Zaber stages
    DEFAULT_HOMING_SPEED = 5            # (mm/s)
    MM_PER_MSTEP = 0.047625 / 1000      # T-NA default microstep size
    DATA_PER_DEG = 12800 / 3            # conversion from degrees to data
    MSTEP_VEL_PER_MM_VEL = 2240         # conversion from mm/s to mstep/sec
    DELTA_T = 24                        # (ms) SET LOWER WHEN WRITING FASTER

    WIPE_GAP = 0.06 #0.03   	        # (mm) 0.03 works well at high focus 0.06 works for lower focus

    LASER_HOME_HEIGHT = 152.8	        # (mm) height of laser stage relative to sample stage
    LASER_MIN_HEIGHT = 140.5	        # (mm) height of laser stage when objective is close to sample stage, at rot = ROT_MAX_ANGLE

    ROTARY_MIN_ANGLE = 0.0	        # (deg) home position of rotary stage near maximum laser height
    ROTARY_MAX_ANGLE = 115	        # (deg) postition of rotary stage at minimum allowable laser height

    # True if writing to a sample to be viewed in microscope (since microscope inverts image)
    INVERT = True;


if __name__ == '__main__':
    main()
