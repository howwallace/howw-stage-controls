
# REFERENCE: https://www.zaber.com/support/docs/api/core-python/0.9/binary.html#binary-module

import sys, time
import keithley_init as kc
from coordinates import V2, V3
from zaber.serial import BinarySerial, BinaryDevice, BinaryCommand, CommandType


GLOBAL_O = V2((0,0))
TR = V2((0,0))
LOCAL_O = V2((0, 0))

"""
# CENTER SQUARE
GLOBAL_O = V2((35.940, 29.300))   # ORIGIN = BOTTOM LEFT
TR = V2((23.887, 16.591))         # TOP RIGHT

REGION_SIZE = GLOBAL_O - TR

# minor adjustments of writing region to prevent overlap without redefining global origin
LOCAL_O = V2((-1.0, 0.6))
"""

CONNECT_KEITHLEY = False
LASER_CURRENT = 0.6


def main():
    define_operating_constants()
    
    if CONNECT_KEITHLEY:
        setup_keithley()
        
    setup_stages()

    move_to(V3((10, 8, 143.9)))
    move_to(V3((10, 20, 143.9)))
    

    """  ****************  FOR REFERENCE  ****************
    move_to(point)
    write_line(start, end, speed)
    write_parallel_lines(start, end, gap, speed, num_lines)
    write_parallel_lines(start, end, gap, speed, delta_speed, num_lines_per_speed, num_speeds)
    write_parallel_angled_lines(start, length, angle, gap, ground_speed, num_lines)
    
    write_circle(speed, rad, cX, cY, "circle");
    write_part_circle(speed, rad, cX, cY, start, end, "part circle");
    write_spiral(speed, rad, gap, cX, cY, turns, "spiral");
    wipe_region(s, x1, y1, x2, y2, vertical, "wipe");
    ******************************************************  """

""
def write_parallel_angled_lines(start, length, angle, gap, speed, num_lines, log_command = False):

    write_parallel_lines(start, start + V2((length, angle), polar = True), gap, speed, num_lines, log_command = log_command)


def write_parallel_lines(start, end, gap, speed, delta_speed, num_lines_per_speed, num_speeds, log_command = False):
    
    for i in range(num_speeds):
        spacer = (num_lines_per_speed + (0.7 if num_lines_per_speed > 1 else 0)) * i * gap
        write_parallel_lines(start + spacer, end + spacer, gap, speed + i*delta_speed, num_lines_per_speed, log_command = log_command)


def write_parallel_lines(start, end, gap, speed, num_lines, log_command = False):

    for i in range(num_lines):
        shift = i * gap
        write_line(start + shift, end + shift, speed, log_command = log_command)
        """
        conserve_middle SIDESTEP NOT NECESSARY SINCE THE LASER TURNS OFF BETWEEN LINES
        """


def write_line(start, end, speed, log_command = False):
    
    if log_command:
        print("LINE: \t%s to %s, %d mm/s" %(start, end, speed))
    
    move_to(start)
    move_to(end, ground_speed = speed, laser_on = True)


def write_circle(center, radius, speed, log_command = False):

    write_part_circle(center, radius, 0, 360, speed, log_command = log_command)

"""
[start], [end] = deg
"""
def write_part_circle(center, radius, start_deg, end_deg, speed, log_command = False):

    if log_command:
        print("PCIRCLE: \tc%s, r%d, (%dº–%dº), %d mm/s" %(center, radius, start, end, speed))

    invert_factor = 1 if INVERT else -1

    f = ground_speed / (1000 * radius)              # (mstep/s) / (1000 * mstep) = 1 / ms
    T = 1000 * 2*math.pi * radius / speed    # (ms)

    start_pos = center + V2((radius, start_deg), polar = True)
    move_to(start_pos)

    start_time = time.perf_counter()

    for t in range(start_deg * T / 360 + DELTA_T, end_deg * T / 360, DELTA_T):
        delta = radius * (V2(f*t) - V2(f*(t - 1)))
        velocity = 1000 * delta / (DELTA_T * 9.375)    # don't really like this...
        data_speed = linspeed2lindata(velocity.magnitude)
        x_linear.move_vel(invert_factor * linspeed2lindata(velocity.x))
        y_linear.move_vel(invert_factor * linspeed2lindata(velocity.y))

        while time.perf_counter() - start_time < t:
            time.sleep(0.001)

    x_linear.stop()
    y_linear.stop()


# [x], [y] = mm;  z = None, or [z] = mm
# ground_speed does not include the speed of changing z;  [ground_speed] = mm/s
def move_to(point, ground_speed = None, laser_on = False):

    if CONNECT_KEITHLEY:
        if not laser_on:
            keith.set_output_off()
        else:
            keith.set_source_current(LASER_CURRENT)

    ground_speed = DEFAULT_HOME_SPEED if ground_speed is None else ground_speed


    pointV2 = point.asV2()  
    dist = point - current_position()
    lin_dist = dist.asV2()        # get the linear components of the distance
    
    lin_dist_data = mm2lindata(lin_dist)
    print(lin_dist)
    z_dist_data = 0 if point.z is None else (mm2rotdata(point.z) - z_rotary.get_position())

    print(lin_dist.unit_x, lin_dist.unit_y)
    x_speed = ground_speed * lin_dist.unit_x
    y_speed = ground_speed * lin_dist.unit_y

    x_time = time_to_move(lin_dist.x, x_speed, LIN_STAGE_ACCELERATION)
    y_time = time_to_move(lin_dist.y, y_speed, LIN_STAGE_ACCELERATION)
    z_time = 0 #time_to_move((z_dist / ROT_STAGE_ACCELERATION)**0.5    # !!! [data] / [mm/s^2]
    
    times = [x_time, y_time, z_time]
    last_to_move = times.index(max(times))
    print(times)

    print("(C) lin_dist_data: %s" %lin_dist_data)


    point_pos_data = mm2posdata(pointV2)    # point data as a position (i.e., given invert, FsOR)
    
    if lin_dist_data.x > 0:
        x_linear.set_target_speed(linspeed2lindata(x_speed))
        x_linear.move_abs(point_pos_data.x, await_reply = (last_to_move == 0))
    if lin_dist_data.y > 0:
        y_linear.set_target_speed(linspeed2lindata(y_speed))
        y_linear.move_abs(point_pos_data.y, await_reply = (last_to_move == 1))
    if z_dist_data == 0:
        z_rotary.move_abs(mm2rotdata(point.z), await_reply = (last_to_move == 2))

    if laser_on:
        keith.set_output_off()

def home_all():
    x_linear.home(await_reply = True)
    y_linear.home(await_reply = True)
    z_rotary.home(await_reply = True)


""" CONVERSIONS """

""" TO DO:  integrate the conversions for linear/rotary ;
    if it's the z component, then we already know that it's rotary...
    no need to convert in a different function """

# converts distance (or V2) in mm to distance in linear stage data
# returns an integer (or V2 of integers)
def mm2lindata(mm):
    if type(mm) is V2:
        return (mm * DATA_PER_MM).round()
    return (int)(mm * DATA_PER_MM)

# converts position (V2) in mm to position in linear stage data,
# considering inversion / global and local frames of reference
# returns a V2 of integers (linear stage data)
def mm2posdata(pos_mm):
    if (INVERT):
        return mm2lindata(GLOBAL_O + LOCAL_O + pos_mm)
    return mm2lindata(GLOBAL_O - LOCAL_O - pos_mm)

def linspeed2lindata(speed):
    return (int)(speed * DATA_PER_MM_SPEED)

def lindata2mm(data):
    return (int)(data / DATA_PER_MM)

# converts laser height in mm to degree-related rotary stage data
# returns an integer
def mm2rotdata(mm):     # (deg) empirical shift;  degrees at 0 mm
    return deg2rotdata(B_EMPIR - DEG_PER_MM * mm)

def rotdata2mm(data):
    return (-rotdata2deg(data) + B_EMPIR) / DEG_PER_MM

def deg2rotdata(deg):
    return (int)(deg * DATA_PER_DEG)

def rotdata2deg(data):
    return (int)(data / DATA_PER_DEG)

# [speed] = mm/s
def linspeed2rotdata(speed):
    return degspeed2rotdata(speed * DEG_PER_MM)

# [speed] = deg/s
def degspeed2rotdata(speed):
    return (int)(speed * DATA_PER_DEG_SPEED)
    

"""
    OVERLOAD WITH SUPPORT FOR VECTORS AND POINTS
    
    MM2LINPOSDATA(MM)
    
    MM2ROTPOSDATA(MM)
    
"""


"""
[dist] = mm
[speed] = mm/s
[accel] = mm/(s^2)
"""
def time_to_move(dist, speed, accel):
    if dist == 0 or speed == 0:
        return 0
    
    dist_always_accel = speed**2 / (2 * accel)
    time_always_accel = (2 * dist_always_accel / accel)**0.5
    
    if dist < dist_always_accel:
        return time_always_accel
    return time_always_accel + (dist - dist_always_accel) / speed

def current_position():
    return V3((lindata2mm(x_linear.get_position()), lindata2mm(y_linear.get_position()), rotdata2mm(z_rotary.get_position())))


""" CONNECTIONS AND SETUP """

def setup_keithley():
    global keith
    keith = kc.Keithley()


def setup_stages():
    global x_linear, y_linear, z_rotary
    
    serial_conn = BinarySerial(STAGES_PORT, timeout = None)
    
    x_linear = BinaryDevice(serial_conn, 2)
    y_linear = BinaryDevice(serial_conn, 3)
    z_rotary = BinaryDevice(serial_conn, 1)
    
    x_linear.set_home_speed(linspeed2lindata(DEFAULT_HOME_SPEED))
    y_linear.set_home_speed(linspeed2lindata(DEFAULT_HOME_SPEED))    

    # need to  check that mm2rotdata does the right conversion
    #rotary.set_target_speed(mm2rotdata(DEFAULT_ROT_SPEED))
    x_linear.set_target_speed(linspeed2lindata(DEFAULT_HOME_SPEED))
    y_linear.set_target_speed(linspeed2lindata(DEFAULT_HOME_SPEED))

    x_linear.set_acceleration(LIN_STAGE_ACCELERATION)
    y_linear.set_acceleration(LIN_STAGE_ACCELERATION)
    z_rotary.set_acceleration(ROT_STAGE_ACCELERATION)

    z_rotary.set_min_position(deg2rotdata(ROTARY_MIN_ANGLE))
    z_rotary.set_max_position(deg2rotdata(ROTARY_MAX_ANGLE))

    home_all()
    


def define_operating_constants():
    
    """         ZABER CONTROL         """
    global STAGES_PORT, MM_PER_MSTEP, DATA_PER_MM, DATA_PER_MM_SPEED, DATA_PER_DEG, DATA_PER_DEG_SPEED, DEG_PER_MM, DELTA_T, DEFAULT_HOME_SPEED, DEFAULT_ROT_SPEED, LIN_STAGE_ACCELERATION, ROT_STAGE_ACCELERATION, WIPE_GAP, ROTARY_MIN_ANGLE, ROTARY_MAX_ANGLE, B_EMPIR, INVERT

    STAGES_PORT = "COM3"                # serial port to Zaber stages
    DATA_PER_MM = 1000 / 0.047625       # conversion from mm to data
    DATA_PER_MM_SPEED = 2240            # conversion from mm/s to data (speed)
    DATA_PER_DEG = 12800 / 3            # conversion from degrees to data
    DATA_PER_DEG_SPEED = 6990           # conversion from deg/s to data (speed)
    DEG_PER_MM = 9.2597                 # (deg/mm) empirical conversion, mm to degrees directly (i.e., not to height in mm) 
    DELTA_T = 24                        # (ms) SET LOWER WHEN WRITING FASTER
    
    DEFAULT_HOME_SPEED = 5              # (mm/s)
    DEFAULT_ROT_SPEED = 10              # (deg/s)
    LIN_STAGE_ACCELERATION = 2000       # (data/s^2) ?
    ROT_STAGE_ACCELERATION = 20         # (data/s^2) ?

    WIPE_GAP = 0.06 #0.03   	        # (mm) 0.03 works well at high focus 0.06 works for lower focus
    
    #LASER_HOME_HEIGHT = 152.8	        # (mm) height of laser stage relative to sample stage
    #LASER_MIN_HEIGHT = 140.5	        # (mm) height of laser stage when objective is close to sample stage, at rot = ROT_MAX_ANGLE

    ROTARY_MIN_ANGLE = 0.0	        # (deg) home position of rotary stage near maximum laser height
    ROTARY_MAX_ANGLE = 120	        # (deg) postition of rotary stage at minimum allowable laser height
    B_EMPIR = 1414.9692                 # (deg) position of rotary stage at 0 mm

    # True if writing to a sample to be viewed in microscope (since microscope inverts image)
    INVERT = True;


if __name__ == '__main__':
    main()

