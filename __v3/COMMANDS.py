
# REFERENCE: https://www.zaber.com/support/docs/api/core-python/0.9/binary.html#binary-module

"""

IF (IN CONSOLE) PRESSING STOP DOES NOT DISPLAY THE CURRENT POSITION, I THINK IT'S PROBABLY BECAUSE DISABLE_AUTO_REPLY IS ON.  RESET DEVICE MODE SUCH THAT BIT 0 = 0.

"""

import sys, time, math, winsound
import keyboard
import keithley_handler as kc
from drawing_handler import MoveMapper
from coordinates import V2, V3
from zaber.serial import BinarySerial, BinaryDevice, BinaryCommand, CommandType



#"""
SAMPLE_NAME = "HW 2020-01-23 A"
GLOBAL_O = V2((35.6, 39.0260))      # ORIGIN = BOTTOM LEFT
TR = V2((21.6566, 25.0))            # TOP RIGHT
LOCAL_O = V2((6.2, 0.5))                # minor adjustments of writing region to prevent overlap without redefining global origin
#"""

""" 
HW 2020-01-23 B
""
GLOBAL_O = V2((35.9, 35.3))         # ORIGIN = BOTTOM LEFT
TR = V2((22.0, 21.0))               # TOP RIGHT
LOCAL_O = V2((1.0, 8.6))            # minor adjustments of writing region to prevent overlap without redefining global origin
#"""

"""
SAMPLE_NAME = "HW_1_19_1"
GLOBAL_O = V2((35.9859, 37.8388))   # ORIGIN = BOTTOM LEFT
TR = V2((21.5373, 25.3594))         # TOP RIGHT
LOCAL_O = V2((9.2, 0))                # minor adjustments of writing region to prevent overlap without redefining global origin
#"""
"""
SAMPLE_NAME = "HW_1_19_2"
GLOBAL_O = V2((34.9637, 38.2244))   # ORIGIN = BOTTOM LEFT
TR = V2((20.8351, 25.2664))         # TOP RIGHT
LOCAL_O = V2((12.5, 10))                # minor adjustments of writing region to prevent overlap without redefining global origin
#"""

REGION_SIZE = GLOBAL_O - TR

CONNECT_ROTARY = True
CONNECT_KEITHLEY = True
POSITION_GETTER_MODE = False    # True if you want to maintain port connection and keyboard control after commands are run
MOVE_MAPPING = False

def main():
    
    try:
        define_operating_constants()
        
        if CONNECT_KEITHLEY:
            setup_keithley()

        ## be sure to call setup_stages() before moving/setting objective height.  Note that there's some give in the rotation of the pin through the microscope coarse control.
        setup_stages()

        if POSITION_GETTER_MODE:
            keyboard.add_hotkey('p', print_position)
            keyboard.wait('esc')    # press esc once you're finished with position-getting

        elif MOVE_MAPPING:
            
            mp = MoveMapper(SAMPLE_NAME, CONNECT_KEITHLEY, DEFAULT_HOME_SPEED)
            mp.draw_map()
            
            if mp.continue_to_run:
                write_commands()

        else:
            # MANUAL COMMAND-CALLING
            # NOTE:  IT IS EXTREMELY IMPORTANT that you move to someplace within the sample region, THEN
            #        adjust stage height;  the minimum rotary position is set such that the objective casing
            #        will not collide with sample holder screws, BUT THIS MINIMUM POSITION IS SET SUCH THAT
            #        THE OBJECTIVE COULD COLLIDE WITH SAMPLE HOLDER SCREWS!

            """ REFERENCE
            write_parallel_lines_vertical_continuous(z, start, end, gap, speed, log_command = False)
            write_parallel_lines_horizontal_continuous(z, start, end, gap, speed, log_command = False)
            write_parallel_lines_horizontal_const_height(z, x_width, speeds, gap, inter_speed_gap_factor = 0.2)
            """

            #write_parallel_lines_horizontal_const_height(144.0, 0.9, [1.4, 1.2, 1.0, 0.8, 0.6, 0.4, 0.2], 0.3)

            """
            write_parallel_lines_horizontal_continuous(144.8, V2((0, 0)), V2((0.9, 0.82)), 0.2, 0.8)
            write_parallel_lines_horizontal_continuous(144.8, V2((0, 1)), V2((0.9, 1.82)), 0.2, 0.6)
            write_parallel_lines_horizontal_continuous(144.8, V2((0, 2)), V2((0.9, 2.82)), 0.2, 0.4)
            """
            
            #WIPING
            """
            write_parallel_lines_horizontal_continuous(145.0, V2((-1, -1)), REGION_SIZE + V2((2, 2)), 0.08, 8)
            #write_parallel_lines_vertical_continuous(145.0, V2((-1, -1)), REGION_SIZE + V2((2, 2)), 0.12, 8)
            #"""
            """
            #write_parallel_lines_horizontal_continuous(145.0, V2((0, 0)), V2((3, 1.8)), 0.08, 8)
            write_parallel_lines_vertical_continuous(145.0, V2((0, 0)), V2((2, 1.8)), 0.08, 8)
            #"""

        winsound.Beep(1000, 500)
        
    # SHIFT-CTRL-C TO INTERRUPT, THEN CLEAN UP
    except KeyboardInterrupt:
        print("--terminated--")
    except:
        print("--unexpected error--")
        raise
    finally:
        clean_up()


def write_commands():

    print("A")
    #outline_region(142.0)

    #wipe_region(147.0, speed = 3)


def write_parallel_angled_lines(start, length, angle, gap, speed, num_lines, log_command = False):

    write_parallel_lines(start, start + V2(angle)*length, gap, speed, num_lines, log_command = log_command)


def write_parallel_lines_delta_s(start, end, gap, speed, delta_speed, num_lines_per_speed, num_speeds, log_command = False):
    
    for i in range(num_speeds):
        spacer = (num_lines_per_speed + (0.7 if num_lines_per_speed > 1 else 0)) * i * gap
        write_parallel_lines(start + spacer, end + spacer, gap, speed + i*delta_speed, num_lines_per_speed, log_command = log_command)


# write parallel lines with spaces: | | | |
# NOTE: start and end define ENDPOINTS OF THE FIRST LINE
def write_parallel_lines_gap(start, end, gap, speed, num_lines, log_command = False):

    direction = end - start
    shift = direction.unit.perpendicular_clk * gap        # in order to write //-  as opposed to -// (perpendicular_cntclk)
    
    for i in range(num_lines):
        write_line(start + shift*i, end + shift*i, speed, log_command = log_command)


# write vertical parallel lines in an egyptian pattern: |-|_|-|_|
# NOTE: doesn't take num_lines as an argument.
# NOTE: unlike other parallel_lines functions, start and end define REGION BOUNDARIES rather than ENDPOINTS OF THE FIRST LINE.
def write_parallel_lines_vertical_continuous(z, start, end, gap, speed, log_command = False):

    shift = V2((gap, 0))
    move_to(start)

    z_rotary.move_abs(mm2rotdata(z), await_reply = True)

    if CONNECT_KEITHLEY:
        keith.set_output_on()
        
    num_lines = int(abs((end - start).x)/float(gap))
    for i in range(0, num_lines, 2):
        if i > 0:
            move_to(start + shift*i, speed)
        move_to(V2((start.x, end.y)) + shift*i, speed)
        move_to(V2((start.x, end.y)) + shift*(i + 1), speed)
        move_to(start + shift*(i + 1), speed)

    if CONNECT_KEITHLEY:
        keith.set_output_off()

    # PRINT OUT WHERE TO SET LOCAL_O NEXT
    print(LOCAL_O + V2((0, abs((end - start).y) + gap)))
    print("OR")
    print(LOCAL_O + V2(((num_lines + 1)*gap, 0)))

    # SHOULD DO THE SAME THING IN THEORY...  HAVEN'T QUITE TESTED...
    """
    # VERTICAL WIPE LINES AT CONSTANT HEIGHT, SPEED    
    y_width = 3.2
    speed = 8
    gap = 0.08
    count = 12
    
    for i in range(count):
        
        start = V2((i*2*gap, 0))
        end = V2((i*2*gap, y_width))
        
        if i == 0:
            move_to(start)
            z_rotary.move_abs(mm2rotdata(145.0), await_reply = True)
        
        write_line(start, end, speed)
        write_line(end + V2((gap, 0)), start + V2((gap, 0)), speed)

    print(LOCAL_O + V2((0, y_width + gap)))
    print("OR")
    print(LOCAL_O + V2((count*2*gap, 0)))
    #"""

# write horizontal parallel lines in a down->up egyptian pattern
# NOTE: doesn't take num_lines as an argument.
# NOTE: unlike other parallel_lines functions, start and end define REGION BOUNDARIES rather than ENDPOINTS OF THE FIRST LINE.
def write_parallel_lines_horizontal_continuous(z, start, end, gap, speed, log_command = False):

    shift = V2((0, gap))
    move_to(start)

    z_rotary.move_abs(mm2rotdata(z), await_reply = True)

    if CONNECT_KEITHLEY:
        keith.set_output_on()

    num_lines = int(abs((end - start).y)/float(gap))
    
    for i in range(0, num_lines, 2):
        if i > 0:
            move_to(start + shift*i, speed)
        move_to(V2((end.x, start.y)) + shift*i, speed)
        move_to(V2((end.x, start.y)) + shift*(i + 1), speed)
        move_to(start + shift*(i + 1), speed)

    if CONNECT_KEITHLEY:
        keith.set_output_off()

    # PRINT OUT WHERE TO SET LOCAL_O NEXT
    print(LOCAL_O + V2((0, (num_lines + 1)*gap)))
    print("OR")
    print(LOCAL_O + V2((abs((end - start).x) + gap, 0)))

    # SHOULD DO THE SAME THING IN THEORY...  HAVEN'T QUITE TESTED...
    """
    # HORIZONTAL WIPE LINES AT CONSTANT HEIGHT, SPEED
    x_width = 1.8
    speed = 8
    gap = 0.08
    count = 10
    
    for i in range(count):
        
        start = V2((0, i*2*gap))
        end = V2((x_width, i*2*gap))
        
        if i == 0:
            move_to(start)
            z_rotary.move_abs(mm2rotdata(145.0), await_reply = True)
        
        write_line(start, end, speed)
        write_line(end + V2((0, gap)), start + V2((0, gap)), speed)
        

    print(LOCAL_O + V2((0, count*2*gap)))
    print("OR")
    print(LOCAL_O + V2((x_width + gap, 0)))
    #"""


# VERTICAL, REGION-TALL LINES
# e.g., write_parallel_lines_vertical_region_tall(145.0, [8, 7, 6, 5], 0.6)
def write_parallel_lines_vertical_region_tall(z, speeds, gap, inter_speed_gap_factor = 0.2):

    z_rotary.move_abs(mm2rotdata(z), await_reply = True)
    
    for i in range(len(speeds)):
        
        start = V2((i*(2 + inter_speed_gap_factor)*gap, -1))
        end = V2((i*(2 + inter_speed_gap_factor)*gap, REGION_SIZE.y + 1))
        
        speed = speeds[i]
        print(speed)
        
        if i == 0:
            move_to(start)
            z_rotary.move_abs(mm2rotdata(z), await_reply = True)

        write_line(start, end, speed)
        write_line(end + V2((gap, 0)), start + V2((gap, 0)), speed)

    print(LOCAL_O + V2(((len(speeds)*(2 + inter_speed_gap_factor) + 1)*gap, 0)))


# HORIZONTAL, REGION-WIDE LINES
# e.g., write_parallel_lines_vertical_region_tall(145.0, [1, 0.8, 0.6, 0.4, 0.2], 0.6)
def write_parallel_lines_horizontal_region_wide(z, speeds, gap, inter_speed_gap_factor = 0.2):

    for i in range(len(speeds)):
        
        start = V2((-1, i*(2 + inter_speed_gap_factor)*gap))
        end = V2((REGION_SIZE.x + 1, i*(2 + inter_speed_gap_factor)*gap))
        
        speed = speeds[i]
        print(speed)
        
        if i == 0:
            move_to(start)
            z_rotary.move_abs(mm2rotdata(z), await_reply = True)

        write_line(start, end, speed)
        write_line(end + V2((0, gap)), start + V2((0, gap)), speed)

    print(LOCAL_O + V2((0, (len(speeds)*(2 + inter_speed_gap_factor) + 1)*gap)))

            
# HORIZONTAL LINES AT CONSTANT HEIGHT
# e.g., write_parallel_lines_horizontal_const_height(145.0, [8, 7, 6, 5], 0.6)
def write_parallel_lines_horizontal_const_height(z, x_width, speeds, gap, inter_speed_gap_factor = 0.2):
            
    for i in range(len(speeds)):
        
        start = V2((0, i*(2 + inter_speed_gap_factor)*gap))
        end = V2((x_width, i*(2 + inter_speed_gap_factor)*gap))
        
        speed = speeds[i]
        print(speed)
        
        if i == 0:
            move_to(start)
            z_rotary.move_abs(mm2rotdata(z), await_reply = True)
        
        write_line(start, end, speed)
        write_line(end + V2((0, gap)), start + V2((0, gap)), speed)
        
    print(LOCAL_O + V2((0, (len(speeds)*(2 + inter_speed_gap_factor) + 1)*gap)))
    print("OR")
    print(LOCAL_O + V2((x_width + gap, 0)))


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

    f = speed / (1000 * radius)              # circle frequency; (mm/s) / (1000 * mm) = 1 / ms
    T = 1000 * 2*math.pi * radius / speed    # time it takes to do a whole circle (ms)

    start_pos = center + V2(start_deg)*radius   # no need for invert_factor--handled in move_to
    move_to(start_pos)

    x_linear.disable_auto_reply()
    y_linear.disable_auto_reply()
    
    start_time = time.perf_counter()

    for t in range(int(start_deg * T / 360) + DELTA_T, int(end_deg * T / 360), DELTA_T):
        
        delta = (V2(180/math.pi * f*t) - V2(180/math.pi * f*(t - DELTA_T))) * radius
        velocity = delta.unit * speed

        # await_reply set to None here because move_vel can't be interrupted by disable_auto_reply
        # (will get busy error response = [_, 255, 255]);  None value just skips setting auto_reply status

        x_linear.move_vel(invert_factor * linspeed2lindata(velocity.x), await_reply = None)
        y_linear.move_vel(invert_factor * linspeed2lindata(velocity.y), await_reply = None)
        
        while time.perf_counter() - start_time < 0.001*t:
            time.sleep(0.001)

    x_linear.stop()
    y_linear.stop()


# [point] = V2 or V3, in mm
# ground_speed does not include the speed of changing z;  [ground_speed] = mm/s
def move_to(point, ground_speed = None, laser_on = False):

    if CONNECT_KEITHLEY:
        if not laser_on:
            keith.set_output_off()
        else:
            keith.set_output_on()
    
    ground_speed = DEFAULT_HOME_SPEED if ground_speed is None else ground_speed


    global_point = local2globalmm(point)        # point data as a position (i.e., given invert, FsOR)
    global_point_data = mm2lindata(global_point)
    
    dist = global_point - current_position()
    lin_dist = V2(dist)                         # get the linear components of the distance
    lin_dist_data = mm2lindata(lin_dist)

    #z_dist_data = 0 if (type(point) is V2 or not CONNECT_ROTARY) else (mm2rotdata(point.z) - z_rotary.get_position())

    veloc = abs(lin_dist.unit) * ground_speed

    x_time = time_to_move(lin_dist.x, veloc.x, LIN_STAGE_ACCELERATION)
    y_time = time_to_move(lin_dist.y, veloc.y, LIN_STAGE_ACCELERATION)
    #z_time = 0 if (type(point) is V2 or not CONNECT_ROTARY) else time_to_move(rotdata2deg(z_dist_data), DEFAULT_ROT_SPEED, ROT_STAGE_ACCELERATION)    # !!! not tested but seems right
    
    times = [x_time, y_time]#, z_time]
    last_to_move = times.index(max(times))

    if abs(lin_dist_data.x) > 0:
        x_linear.set_target_speed(linspeed2lindata(veloc.x), await_reply = True)
    if abs(lin_dist_data.y) > 0:
        y_linear.set_target_speed(linspeed2lindata(veloc.y), await_reply = True)

    # this is super ugly but it has to go like this procedurally, such that the command "await_reply"-ing (i.e., the slowest move) is the last one called 
    if last_to_move == 0:
        if abs(lin_dist_data.y) > 0:
            y_linear.move_abs(global_point_data.y)                     # don't await reply if x-axis will be slowest (necessary for simultaneous moves)
        #if abs(z_dist_data) > 0:
        #    z_rotary.move_abs(mm2rotdata(point.z))                  # don't await reply if x-axis will be slowest
        if abs(lin_dist_data.x) > 0:
            x_linear.move_abs(global_point_data.x, await_reply = True)
    elif last_to_move == 1:
        if abs(lin_dist_data.x) > 0:
            x_linear.move_abs(global_point_data.x)                     # don't await reply if y-axis will be slowest
        #if abs(z_dist_data) > 0:
        #    z_rotary.move_abs(mm2rotdata(point.z))                  # don't await reply if y-axis will be slowest
        if abs(lin_dist_data.y) > 0:
            y_linear.move_abs(global_point_data.y, await_reply = True)
    """
    elif last_to_move == 2:
        if abs(lin_dist_data.x) > 0:
            x_linear.move_abs(global_point_data.x)                     # don't await reply if rotary will be slowest
        if abs(lin_dist_data.y) > 0:
            y_linear.move_abs(global_point_data.y)                     # don't await reply if rotary will be slowest
        if abs(z_dist_data) > 0:
            z_rotary.move_abs(mm2rotdata(point.z), await_reply = True)
    """
    
    if CONNECT_KEITHLEY and laser_on:
        keith.set_output_off()


# z = stage height;  [z] = mm
def outline_region(z, speed = None):

    move_to(V2((-0.1, -0.1)) + LOCAL_O * (-1 if INVERT else 1))
    z_rotary.move_abs(mm2rotdata(z), await_reply = True)

    if CONNECT_KEITHLEY:
        keith.set_output_on()

    move_to(V2((-0.1, REGION_SIZE.y + 0.1)) + LOCAL_O * (-1 if INVERT else 1), speed)
    move_to(REGION_SIZE + V2((0.1, 0.1)) + LOCAL_O * (-1 if INVERT else 1), speed)
    move_to(V2((REGION_SIZE.x + 0.1, -0.1)) + LOCAL_O * (-1 if INVERT else 1), speed)
    move_to(V2((-0.1, -0.1)) + LOCAL_O * (-1 if INVERT else 1), speed)

    if CONNECT_KEITHLEY:
        keith.set_output_off()


def wipe_region(z, speed = None):
    
    move_to(V2((-1, 0)) + LOCAL_O * (-1 if INVERT else 1))
    z_rotary.move_abs(mm2rotdata(z), await_reply = True)

    if CONNECT_KEITHLEY:
        keith.set_output_on()

    for i in range(int(REGION_SIZE.y / (2*WIPE_GAP)) + 1):
        if i > 0:
            move_to(V2((-1, WIPE_GAP * 2*i))                    + LOCAL_O * (-1 if INVERT else 1), speed)
        move_to(V2((REGION_SIZE.x + 1, WIPE_GAP * 2*i))         + LOCAL_O * (-1 if INVERT else 1), speed)
        move_to(V2((REGION_SIZE.x + 1, WIPE_GAP * (2*i + 1)))   + LOCAL_O * (-1 if INVERT else 1), speed)
        move_to(V2((-1, WIPE_GAP * (2*i + 1)))                  + LOCAL_O * (-1 if INVERT else 1), speed)

    if CONNECT_KEITHLEY:
        keith.set_output_off()


def home_all():
    # await_reply must = True for all homing commands, otherwise there'll be 'busy' errors because the succeeding commands will be called before homing is complete
    if CONNECT_ROTARY:
        z_rotary.home(await_reply = True)
    x_linear.home(await_reply = True)
    y_linear.home(await_reply = True)

""" CONVERSIONS """

""" TO DO:  integrate the conversions for linear/rotary ;
    if it's the z component, then we already know that it's rotary...
    no need to convert in a differnt function """

# converts distance (or V2) in mm to distance in linear stage data
# returns an integer (or V2 of integers)
def mm2lindata(mm):
    if type(mm) is V2:
        return (mm * DATA_PER_MM).round()
    return (int)(mm * DATA_PER_MM)

# converts position (V2) in mm to position in linear stage data,
# considering inversion / global and local frames of reference
# returns a V2 of integers (linear stage data)
def local2globalmm(local_mm):
    if (INVERT):
        return TR + LOCAL_O + local_mm
    return GLOBAL_O - LOCAL_O - local_mm

# ALWAYS int-cast when converting real units to data.
def linspeed2lindata(speed):
    return (int)(speed * DATA_PER_MM_SPEED)

# NEVER int-cast when converting data to a real unit.
def lindata2mm(data):
    return data / DATA_PER_MM

# converts laser height in mm to degree-related rotary stage data
# returns an integer
def mm2rotdata(mm):     # (deg) empirical shift;  degrees at 0 mm
    return deg2rotdata(B_EMPIR - DEG_PER_MM * mm)

def rotdata2mm(data):
    return (-rotdata2deg(data) + B_EMPIR) / DEG_PER_MM

def deg2rotdata(deg):
    return (int)(deg * DATA_PER_DEG)

def rotdata2deg(data):
    return data / DATA_PER_DEG

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
[accel] = mm/s^2
"""
def time_to_move(dist, speed, accel):
    if mm2lindata(dist) == 0 or linspeed2lindata(speed) == 0:
        return 0

    dist = abs(dist)
    
    dist_always_accel = speed**2 / (2 * accel)
    time_always_accel = (2 * dist_always_accel / accel)**0.5
    
    if dist < dist_always_accel:
        return time_always_accel
    return time_always_accel + (dist - dist_always_accel) / speed

def current_position():
    if CONNECT_ROTARY:
        return V3((lindata2mm(x_linear.get_position()), lindata2mm(y_linear.get_position()), rotdata2mm(z_rotary.get_position())))
    return V2((lindata2mm(x_linear.get_position()), lindata2mm(y_linear.get_position())))

def print_position():
    print(current_position())
    

""" CONNECTIONS AND SETUP """

def setup_keithley():
    global keith

    keith = kc.Keithley()

    keith.set_source_current(0.4)
    keith.set_voltage_compliance(21.0)
    keith.set_output_on()


def setup_stages():
    global serial_conn, x_linear, y_linear, z_rotary
    
    serial_conn = BinarySerial(STAGES_PORT, timeout = None)
    
    if CONNECT_ROTARY:
        z_rotary = BinaryDevice(serial_conn, 1)
        z_rotary.set_home_speed(degspeed2rotdata(DEFAULT_ROT_SPEED))
        z_rotary.set_target_speed(degspeed2rotdata(DEFAULT_ROT_SPEED))
        z_rotary.set_acceleration(ROT_STAGE_ACCELERATION)

        z_rotary.set_min_position(deg2rotdata(ROTARY_MIN_ANGLE))
        z_rotary.set_max_position(deg2rotdata(ROTARY_MAX_ANGLE))
    
    x_linear = BinaryDevice(serial_conn, 2)
    y_linear = BinaryDevice(serial_conn, 3)
    
    x_linear.set_home_speed(linspeed2lindata(DEFAULT_HOME_SPEED))
    y_linear.set_home_speed(linspeed2lindata(DEFAULT_HOME_SPEED))

    x_linear.set_target_speed(linspeed2lindata(DEFAULT_HOME_SPEED))
    y_linear.set_target_speed(linspeed2lindata(DEFAULT_HOME_SPEED))

    x_linear.set_acceleration(LIN_STAGE_ACCELERATION)
    y_linear.set_acceleration(LIN_STAGE_ACCELERATION)

    x_linear.disable_manual_move_tracking()
    y_linear.disable_manual_move_tracking()

    home_all()


def clean_up():
    print("cleaning up")

    """
    if CONNECT_KEITHLEY:
        keith.set_output_off()
    """
    
    home_all()
    
    x_linear.set_target_speed(linspeed2lindata(DEFAULT_HOME_SPEED))
    y_linear.set_target_speed(linspeed2lindata(DEFAULT_HOME_SPEED))

    x_linear.enable_auto_reply()
    y_linear.enable_auto_reply()
    
    serial_conn.close()
    print("finished")


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
    DEFAULT_ROT_SPEED = 15              # (deg/s)
    LIN_STAGE_ACCELERATION = 2000       # (data/s^2) ?
    ROT_STAGE_ACCELERATION = 40         # (data/s^2) ?

    WIPE_GAP = 0.4        	        # (mm) obviously depends on focal distance and power. 0.05 is right for z = 142.0, P = 120 mW
    
    #LASER_HOME_HEIGHT = 152.8	        # (mm) height of laser stage relative to sample stage
    #LASER_MIN_HEIGHT = 140.5	        # (mm) height of laser stage when objective is close to sample stage, at rot = ROT_MAX_ANGLE

    ROTARY_MIN_ANGLE = 0.0	        # (deg) home position of rotary stage near maximum laser height (152.81 mm)
    ROTARY_MAX_ANGLE = 113.5	        # (deg) postition of rotary stage at minimum allowable laser height (140.55 mm)
    B_EMPIR = 1414.9692                 # (deg) position of rotary stage at 0 mm

    # True if writing to a sample to be viewed in microscope (since microscope inverts image)
    INVERT = True;


if __name__ == '__main__':
    main()



# SOME MORE-OBSCURE COMMAND SEQUENCES

    """ VERTICAL LINES AT DIFFERENT STAGE HEIGHTS
    x_width = 0.35
    y_width = 0.9
    inter_region_gap = 0.1

    speeds = [1, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
    set_x_shift = V2((x_width + inter_region_gap, 0))
    set_y_shift = V2((0, y_width + inter_region_gap))     # shift between sets of parallel lines, grouped by z
    print(LOCAL_O + set_x_shift*len(speeds) + set_y_shift*9 + V2((0.2, 0)))

    for i in range(len(speeds)):

        z_rotary.home(await_reply = True)

        speed = speeds[i]
        z_start = 145.2
        z_shift = 0.4
        
        start = V2((0, 0)) + set_x_shift*i
        end = V2((x_width, y_width)) + set_x_shift*i
        gap = 0.08

        print(speed)
        move_to(start)

        for j in range(9):
            z_rotary.move_abs(mm2rotdata(z_start - z_shift*j), await_reply = True)
            write_parallel_lines_vertical_continuous(start + set_y_shift*j, end + set_y_shift*j, gap, speed)
    #"""
            
    """ HORIZONTAL LINES
    speeds = [5, 4, 3, 2, 1, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
    set_shift = V2((0,0.36))     # shift between sets of parallel lines, grouped by z
    print(LOCAL_O + set_shift*9 + V2((0, 0.16)))

    for i in range(len(speeds)):

        z_rotary.home(await_reply = True)

        speed = speeds[i]
        z_start = 145.2
        z_shift = 0.4
        
        end = V2((0.9 + i,0.35))
        start = V2((0 + i,0))
        gap = 0.08

        print(speed)
        move_to(start)
        
        for j in range(9):
            z_rotary.move_abs(mm2rotdata(z_start - z_shift*j), await_reply = True)
            write_parallel_lines_horizontal_continuous(start + set_shift*j, end + set_shift*j, gap, speed)
    #"""


# OLD:
"""  ****************  FOR REFERENCE  ****************
move_to(point)
write_line(start, end, speed)
write_parallel_lines(start, end, gap, speed, num_lines)
write_parallel_lines(start, end, gap, speed, delta_speed, num_lines_per_speed, num_speeds)
write_parallel_angled_lines(start, length, angle, gap, ground_speed, num_lines)

write_circle(center, radius, speed, log_command = False)
write_part_circle(center, radius, start_deg, end_deg, speed, log_command = False):
write_circle(speed, rad, cX, cY, "circle");
write_part_circle(speed, rad, cX, cY, start, end, "part circle");
write_spiral(speed, rad, gap, cX, cY, turns, "spiral");
wipe_region(s, x1, y1, x2, y2, vertical, "wipe");
******************************************************  """
