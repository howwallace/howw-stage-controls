"""
DIRECTORY:	https://github.com/howwallace/howw-stage-controls.git
PROGRAM:	execute_commands.py
AUTHOR:		Harper O. W. Wallace
DATE:		9 Apr 2020

DESCRIPTION:
Executes move commands for Zaber Technologies rotary (1 x X-RSW60A) and
linear (2 x T-LSM050A) stages, all using binary encoding, and supervises
voltage and current control of Keithley 2400 SourceMeter to open and
close a Thorlabs SH05 beam shutter.

Communication with Zaber stages is achieved using a heavily modified
version of Zaber's Serial Library[1], and relies on zaber/serial/*. Cf.
zaber/serial/binaryserial.py for more details. The short of it is: I
would recommend not changing these files.

Communication and control over the Keithley is achieved using a module
published by T. Max Roberts[2], and relies on keithley_handler.py.

PLEASE CONSULT README.md FOR AN OVERVIEW OF THE DESIGN OF THIS LIBRARY,
AND ALSO FOR PRACTICAL, TROUBLESHOOTING, AND REFERENCE INFORMATION.


LINKS:
[1] https://www.zaber.com/support/docs/api/core-python/0.6/ (available
      in this repo, with modifications, in zaber/serial/)
[2] https://github.com/maxroberts/Keithley-2400-SourceMeter-Python-Int
      erface/blob/master/keithley_serial.py (link is broken, but the
      code is available in this repo in keithley_handler.py)
"""


# PARAMETERS FOR TESTING CONDITIONS
# Modify Keithley/stage connections for particular testing conditions
#   e.g., don't bother moving the rotary if you're testing movement in
#   the plane DUMMY_CONNECTIONS effectively overrides CONNECT_ROTARY and
#   CONNECT_KEITHLEY e.g., D_C == True, these devices won't connect even
#   if C_R or C_K == True.
# MAC_TESTING determines what modules are imported (OS limitations)

DUMMY_CONNECTIONS = True
CONNECT_ROTARY = True
CONNECT_KEITHLEY = True
MAC_TESTING = True


import sys, time, math, re
from mapping_handler import MappingHandler
from coordinates import V2

# these modules are not available on mac
if not MAC_TESTING:
    import winsound
    import keyboard

if not DUMMY_CONNECTIONS:
    import keithley_handler as kc
    from zaber.serial import BinarySerial, BinaryDevice, BinaryCommand, CommandType


# POSITION_GETTER_MODE
# Allows you to move stages manually and press 'p' (on your keyboard) to
#   print out stage positions to the console. It's useful for defining
#   corners of sample regions: run execute_commands.py, navigate to the
#   sample origin using linear stage manual control knobs, and press 'p'
#   on the keyboard to print out their position. Press 'esc' to exit
#   POSITION_GETTER_MODE.
# MOVE_MAPPING
# Allows you to visualize how commands will run before you put the
#   sample under the laser. True: then commands are given in a file that
#   corresponds to the sample of interest, which file keeps track of
#   historical read-write information so that the same commands can be
#   executed again; False: then commands must be must bespecified
#   directly in this file.

POSITION_GETTER_MODE = False
MOVE_MAPPING = True


# SAMPLE_NAME
# To access the relevant sample's .txt data file (at SAMPLES_PATH +
#   SAMPLE_NAME + ".txt") to define origins (GLOBAL_O and TR) for manual
#   command-calling. This file also stores historical write information
#   and is where new commands ought to be entered if (a) you are
#   interested in using the MOVE_MAPPING feature, or (b) you'd like to
#   keep a record of the writes you've made to this sample.

SAMPLES_PATH = "/Users/harperwallace/Dropbox/GitHub/howw-stage-controls/samples/"
SAMPLE_NAME = "_waveguide"
#SAMPLE_NAME = "HW 2020-01-23 A"
#SAMPLE_NAME = "HW 2020-01-23 B"
#SAMPLE_NAME = "HW_1_19_1"
#SAMPLE_NAME = "HW_1_19_2"


def main():

    try:
        define_operating_constants()

        # Doesn't do anything if !CONNECT_KEITHLEY or fake connections
        setup_keithley()

        # Be sure to call setup_stages() before moving/setting objective height
        # Note that there's some give in the rotation of the pin through
	#   the microscope coarse control
        setup_stages()

        if POSITION_GETTER_MODE:

            # Press 'p' to print current position to console
            keyboard.add_hotkey('p', print_position)
            # Press 'esc' once you're finished with position-getting
            keyboard.wait('esc')


        elif MOVE_MAPPING:

            mh = MappingHandler(SAMPLES_PATH, SAMPLE_NAME, (CONNECT_KEITHLEY if not DUMMY_CONNECTIONS else False), DEFAULT_HOME_SPEED)
            mh.draw_map()

            if mh.continue_to_run:
                write_mapped_commands(mh.new_cmds_array)
                mh.update_sample_history()

        else:
            # MANUAL COMMAND-CALLING
            # EXTREMELY IMPORTANT NOTES:
            # 1. DON'T LET THE OBJECTIVE LENS HIT THE SAMPLE HOLDER SCREWS.
            # 2. DON'T MELT THE BEAM SHUTTER BY LEAVING THE LASER ON IT TOO LONG.
            # (details in README.md)

            # Extract GLOBAL_O and TR from the sample's corresponding .txt file.
            # Note that if GLOBAL_O appears in a line below TR for some
            #   reason, then GLOBAL_O won't be read (i.e., don't change the
            #   order of GLOBAL_O and TR from the template file).
            try:
                log_file = open(SAMPLES_PATH + SAMPLE_NAME + ".txt", "r")
                for line in log_file.readlines():
                    if len(line.rstrip()) > 0 and line[0] != "#":
                        stripped_line = line.split("#")[0].rstrip()
                        if stripped_line.find("=") != -1 and stripped_line.find("=") < stripped_line.find("("):
                            val = stripped_line.split("=",1)[0].rstrip()                        
                            args = list(map(float, re.sub("[^0-9.,]","", stripped_line.split("=",1)[1].replace("V2","").replace("V3","")).split(",")))
                            if val == "GLOBAL_O":
                                GLOBAL_O = V2((args[0], args[1]))
                            elif val == "TR":
                                TR = V2((args[0], args[1]))
                                REGION_SIZE = GLOBAL_O - TR
                                break
            except FileNotFoundError:
                print("SAMPLE FILE NOT FOUND. USING GENERIC ORIGINS.")

	    # Move writing region without redefining global origins
            LOCAL_O = V2((0, 0))

            ## BEGIN MANUAL COMMANDS:

            




            ## END MANUAL COMMANDS
            
            """ REFERENCE: 
            write_parallel_lines_gap(z, start, end, gap, speed, num_lines):
            write_parallel_lines_vertical_continuous(z, start, end, gap, speed):
            write_parallel_lines_horizontal_continuous(z, start, end, gap, speed):
            write_parallel_lines_vertical_region_tall(z, speeds, gap, inter_speed_gap_factor = 0.2):
            write_parallel_lines_horizontal_region_wide(z, speeds, gap, inter_speed_gap_factor = 0.2):
            write_parallel_lines_horizontal_const_height(z, x_width, speeds, gap, inter_speed_gap_factor = 0.2):
            write_parallel_lines_delta_s(z, start, end, gap, speed, delta_speed, num_lines_per_speed, num_speeds):
            write_line(start, end, speed):
            write_circle(center, radius, speed):
            write_part_circle(center, radius, start_deg, end_deg, speed):
            outline_region(z, speed = None):
            wipe_region(z, gap = 0.08, speed = None):
            move_to(point, ground_speed = None, laser_on = False):
            home_all():
            """

        if not MAC_TESTING:
            # Make a little beep noise so I know it's all finished
            winsound.Beep(1000, 500)

    # SHIFT-CTRL-C TO INTERRUPT, THEN CLEAN UP
    except KeyboardInterrupt:
        print("--terminated--")
    except:
        print("--unexpected error--")
        raise
    finally:
        clean_up()


# Sends new commands in the sample's data file (after mapping by
#   MappingHandler and user confirmation) to stages for writing.
# NOTE: Definitions and re-definitions of LOCAL_O are already taken into
#   account; the position arguments passed to these commands are already
#   adjusted appropriately, so there is no need to adjust that value
#   between writes in this method.
def write_mapped_commands(cmds):
    
    LOCAL_O = V2((0,0))

    for cmd_args in cmds:
        if cmd_args[0] == "write_parallel_lines_vertical_continuous":
            write_parallel_lines_vertical_continuous(*cmd_args[1:])
        elif cmd_args[0] == "write_parallel_lines_horizontal_continuous":
            write_parallel_lines_horizontal_continuous(*cmd_args[1:])
        elif cmd_args[0] == "write_parallel_lines_vertical_region_tall":
            write_parallel_lines_vertical_region_tall(*cmd_args[1:])
        elif cmd_args[0] == "write_parallel_lines_horizontal_region_wide":
            write_parallel_lines_horizontal_region_wide(*cmd_args[1:])
        elif cmd_args[0] == "write_parallel_lines_horizontal_const_height":
            write_parallel_lines_horizontal_const_height(*cmd_args[1:])
        elif cmd_args[0] == "write_parallel_lines_gap":
            write_parallel_lines_gap(*cmd_args[1:])
        elif cmd_args[0] == "write_parallel_lines_delta_s":
            write_parallel_lines_delta_s(*cmd_args[1:])
        elif cmd_args[0] == "write_line":
            write_line(*cmd_args[1:])
        elif cmd_args[0] == "write_circle":
            write_circle(*cmd_args[1:])
        elif cmd_args[0] == "write_part_circle":
            write_part_circle(*cmd_args[1:])
        elif cmd_args[0] == "outline_region":
            outline_region(*cmd_args[1:])
        elif cmd_args[0] == "wipe_region":
            wipe_region(*cmd_args[1:])
        elif cmd_args[0] == "move_to":
            move_to(*cmd_args[1:])
            

# WRITE PARALLEL LINES: VERTICAL, CONTINUOUS
# Writes vertical parallel lines in an egyptian pattern: |-|_|-|_|
# NOTE: unlike other parallel_lines functions, start and end define
#   REGION BOUNDARIES rather than ENDPOINTS OF THE FIRST LINE. This
#   means that vertical, parallel lines will be written in order to fill
#   a rectangle with bottom-left corner = start + LOCAL_O, top-right
#   corner = end + LOCAL_O.
# NOTE: doesn't take num_lines as an argument.
# e.g., write_parallel_lines_vertical_continuous(
#                145.0, V2((0,0)), V2((2.3,1.3)), 0.2, 5)
def write_parallel_lines_vertical_continuous(z, start, end, gap, speed):

    if DUMMY_CONNECTIONS:
        return

    shift = V2((gap, 0))
    move_to(start)

    z_rotary.move_abs(mm2rotdata(z), await_reply = True)

    if CONNECT_KEITHLEY:
        kh.set_output_on()

    num_lines = int(abs((end - start).x)/float(gap))

    for i in range(0, num_lines, 2):

        if i > 0:
            move_to(start + shift*i, speed)
        move_to(V2((start.x, end.y)) + shift*i, speed)
        move_to(V2((start.x, end.y)) + shift*(i + 1), speed)
        move_to(start + shift*(i + 1), speed)

    if CONNECT_KEITHLEY:
        kh.set_output_off()

    # PRINT OUT WHERE TO MANUALLY SET LOCAL_O NEXT
    if not MOVE_MAPPING:
        print(LOCAL_O + V2((0, abs((end - start).y) + gap)))
        print("OR")
        print(LOCAL_O + V2(((num_lines + 1)*gap, 0)))


# WRITE PARALLEL LINES: HORIZONTAL, CONTINUOUS
# Writes horizontal parallel lines in a down->up egyptian pattern
# NOTE: doesn't take num_lines as an argument.
# NOTE: unlike other parallel_lines functions, start and end define
#   REGION BOUNDARIES rather than ENDPOINTS OF THE FIRST LINE.
# e.g., write_parallel_lines_horizontal_continuous(
#                145.0, V2((0,0)), V2((2.3,1.3)), 0.2, 5)
def write_parallel_lines_horizontal_continuous(z, start, end, gap, speed):

    if DUMMY_CONNECTIONS:
        return
    
    shift = V2((0, gap))
    move_to(start)

    z_rotary.move_abs(mm2rotdata(z), await_reply = True)

    if CONNECT_KEITHLEY:
        kh.set_output_on()

    num_lines = int(abs((end - start).y)/float(gap))

    for i in range(0, num_lines, 2):
        if i > 0:
            move_to(start + shift*i, speed)
        move_to(V2((end.x, start.y)) + shift*i, speed)
        move_to(V2((end.x, start.y)) + shift*(i + 1), speed)
        move_to(start + shift*(i + 1), speed)

    if CONNECT_KEITHLEY:
        kh.set_output_off()

    # PRINT OUT WHERE TO SET LOCAL_O NEXT
    if not MOVE_MAPPING:
        print(LOCAL_O + V2((0, (num_lines + 1)*gap)))
        print("OR")
        print(LOCAL_O + V2((abs((end - start).x) + gap, 0)))


# WRITE PARALLEL LINES: VERTICAL, REGION-TALL
# Writes vertical lines that extend from LOCAL_O.y to LOCAL_O.y +
#   REGION_SIZE.y, with additional padding of 1 mm on each side. Two
#   such lines are written at each speed (mm/s) enumerated in speeds.
#   Inter-speed gap factor inflates the gap between same-speed line
#   pairs, so lines written at different speeds  can be more easily
#   distinguished and counted under the microscope. The laser stage
#   height adjusts according to z, *after* the linear stages move to the
#   starting position.
# e.g., write_parallel_lines_vertical_region_tall(
#                145.0, [8, 7, 6, 5], 0.6)
def write_parallel_lines_vertical_region_tall(z, speeds, gap, inter_speed_gap_factor = 0.2):

    if DUMMY_CONNECTIONS:
        return

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

    if not MOVE_MAPPING:
    	print(LOCAL_O + V2(((len(speeds)*(2 + inter_speed_gap_factor) + 1)*gap, 0)))


# HORIZONTAL, REGION-WIDE LINES
# Writes horizontal lines that extend from LOCAL_O.x to LOCAL_O.x +
#   REGION_SIZE.x, with additional padding of 1 mm on each side. Two
#   such lines are written at each speed (mm/s) enumerated in speeds.
#   Inter-speed gap factor inflates the gap between same-speed line
#   pairs, so lines written at different speeds  can be more easily
#   distinguished and counted under the microscope. The laser stage
#   height adjusts according to z, *after* the linear stages move to the
#   starting position.
# e.g., write_parallel_lines_vertical_region_tall(
#                145.0, [1, 0.8, 0.6, 0.4, 0.2], 0.6)
def write_parallel_lines_horizontal_region_wide(z, speeds, gap, inter_speed_gap_factor = 0.2):

    if DUMMY_CONNECTIONS:
        return

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

    if not MOVE_MAPPING:
    	print(LOCAL_O + V2((0, (len(speeds)*(2 + inter_speed_gap_factor) + 1)*gap)))


# WRITE HORIZONTAL LINES AT CONSTANT HEIGHT
# Writes horizontal lines that extend from LOCAL_O.x to LOCAL_O.x +
#   REGION_SIZE.x, with additional padding of 1 mm on each side. Two
#   such lines are written at each speed (mm/s) enumerated in speeds.
#   Inter-speed gap factor inflates the gap between same-speed line
#   pairs, so lines written at different speeds  can be more easily
#   distinguished and counted under the microscope. The laser stage
#   height adjusts according to z, *after* the linear stages move to the
#   starting position.
# e.g., write_parallel_lines_horizontal_const_height(
#                145.0, [8, 7, 6, 5], 0.6)
def write_parallel_lines_horizontal_const_height(z, x_width, speeds, gap, inter_speed_gap_factor = 0.2):

    if DUMMY_CONNECTIONS:
        return

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

    if not MOVE_MAPPING:
        print(LOCAL_O + V2((0, (len(speeds)*(2 + inter_speed_gap_factor) + 1)*gap)))
        print("OR")
        print(LOCAL_O + V2((x_width + gap, 0)))


# WRITE PARALLEL LINES WITH A CONSTANT GAP
# Write parallel lines with spaces: | | | |
# If gap is positive, then parallel lines are written along the axis
#   clockwise-perpendicular to the vector, (end - start). This means
#   that if the lines are vertical, and if start is below end, lines are
#   written left to right;  but if the lines are horizontal, and if
#   start is to the left of end, then lines are written top to bottom.
#   This all is mapped out by MappingHandler, but you should consider it
#   when designing parallel_lines_gap moves.
# NOTE: start and end define ENDPOINTS OF THE FIRST LINE. Additional
#   lines will be written parallal, and approximately to the right,
#   depending on the exact angle between start and end, at a
#   perpendicular distance of gap.
# e.g., write_parallel_lines_gap(
#                145.0, V2((0.0,0.3)), V2((1,0)), -0.2, 1, 5)	
def write_parallel_lines_gap(z, start, end, gap, speed, num_lines):

    if DUMMY_CONNECTIONS:
        return

    direction = end - start

    # in order to write //-  as opposed to -// (perpendicular_cntclk)
    shift = direction.unit.perpendicular_clk * gap

    for i in range(num_lines):
        
        if i == 0:
            move_to(start)
            z_rotary.move_abs(mm2rotdata(z), await_reply = True)

        write_line(start + shift*i, end + shift*i, speed)


# WRITE PARALLEL LINES WITH A SPEED INCREMENT
# Writes parallel lines at different speeds, starting at speed and
#   increasing by delta_speed for every num_lines_per_speed lines
#   written at that temporary speed. num_speeds determines how many
#   times this outer loop iterates, and hence how many total lines are
#   written = num_lines_per_speed * num_speeds
# If gap is positive, then parallel lines are written along the axis
#   clockwise-perpendicular to the vector, (end - start). This means
#   that if the lines are vertical, and if start is below end, lines are
#   written left to right;  but if the lines are horizontal, and if
#   start is to the left of end, then lines are written top to bottom.
#   This all is mapped out by MappingHandler, but you should consider it
#   when designing write_parallel_lines_delta_s moves.
# NOTE: start and end define ENDPOINTS OF THE FIRST LINE. Additional
#   lines will be written parallel, and approximately to the right,
#   depending on the exact angle between start and end, at a
#   perpendicular distance of gap.
# e.g., write_parallel_lines_delta_s(
#                145.0, V2((0.0,0.3)), V2((1,0)), -0.2, 1, 1, 3, 3)	
def write_parallel_lines_delta_s(z, start, end, gap_dist, speed, delta_speed, num_lines_per_speed, num_speeds):

    if DUMMY_CONNECTIONS:
        return
    
    direction = end - start

    # in order to write //-  as opposed to -// (perpendicular_cntclk)
    shift = direction.unit.perpendicular_clk * gap_dist

    for i in range(num_speeds):
        spacer = shift * (num_lines_per_speed + (0.7 if num_lines_per_speed > 1 else 0)) * i
        write_parallel_lines_gap(z, start + spacer, end + spacer, gap_dist, speed + i*delta_speed, num_lines_per_speed)


# WRITE LINE
# Writes a single line from start to end, at the given speed
def write_line(start, end, speed):

    if DUMMY_CONNECTIONS:
        return

    move_to(start)
    move_to(end, ground_speed = speed, laser_on = True)

# WRITE CIRCLE
# Just calls write_part_circle for start = 0, end = 360
def write_circle(center, radius, speed):

    if DUMMY_CONNECTIONS:
        return

    write_part_circle(center, radius, 0, 360, speed)


# WRITE PART CIRCLE
# Writes arcs by calling move_vel (i.e., move at constant speed) on the
#   x- and y- stages at ~differential time increments (defined in
#   milliseconds by DELTA_T). This is far and away the most complicated
#   move function, not least because of the idiosyncrasies of how the
#   Zaber stages handle commands, which makes it necessary to keep track
#   of time programmatically (rather than waiting for the device to
#   respond that it's finished). The key point is that circles can be
#   finicky.
"""
[start], [end] = deg
"""
def write_part_circle(center, radius, start_deg, end_deg, speed):

    if DUMMY_CONNECTIONS:
        return

    invert_factor = 1 if INVERT_COORDINATES else -1

    # f = circle frequency; (mm/s) / (1000 * mm) = 1 / ms
    f = speed / (1000 * radius)
    # T = period = time it takes to do a whole circle (ms)
    T = 1000 * 2*math.pi * radius / speed

    # no need for invert_factor--handled in move_to
    start_pos = center + V2(start_deg)*radius
    move_to(start_pos)

    x_linear.disable_auto_reply()
    y_linear.disable_auto_reply()

    start_time = time.perf_counter()

    for t in range(int(start_deg * T / 360) + DELTA_T, int(end_deg * T / 360), DELTA_T):

        delta = (V2(180/math.pi * f*t) - V2(180/math.pi * f*(t - DELTA_T))) * radius
        velocity = delta.unit * speed

        # await_reply set to None here because move_vel can't be
        # interrupted by disable_auto_reply (will get busy error
        # response = [_, 255, 255]);  None value just skips setting
        # auto_reply status

        x_linear.move_vel(invert_factor * linspeed2lindata(velocity.x), await_reply = None)
        y_linear.move_vel(invert_factor * linspeed2lindata(velocity.y), await_reply = None)

        while time.perf_counter() - start_time < 0.001*t:
            time.sleep(0.001)

    x_linear.stop()
    y_linear.stop()


# MOVE TO
# Moves to the specified point (V2) at a given ground_speed (mm/s),
#   which does not include the speed of changing z. As written, move_to
#   only moves in the plane, and z-stage controls must be passed
#   separately. However, it may become useful in the future to integrate
#   in-plane and z-axis controls so they are handled by the same
#   methods; cf. V3 (a three-dimensioned vector object) in older
#   versions of this file and of coordinates module (__v3/
#   execute_commands.py and /coordinates.py) for a head start on this.
# NOTE: A key feature of move_to is that it is able to handle
#   simultaneous moves by calculating the time that each stage is
#   expected to take, and awaiting a reply only from the slower-moving
#   stage. Though this design is not as useful for simultaneous moves
#   only in the x-y plane (where ground_speed is separated into x- and
#   y- components such that both linear stages should take the same
#   amount of time to complete a given move), it is very useful if
#   z-axis commands are handled together with x-y commands, since the
#   rotary stage moves slowly (cf. EXTREMELY IMPORTANT NOTE #3 in
#   README.md). As above, cf. older versions of this file in (__v3/)
#   for a head start at achieving this.
# NOTE: This makes use of the method time_to_move (below) to predict
#   move times. Cf. the notes on that method.
"""
[point] = V2, in mm
[ground_speed] = mm/s; if value == None, => DEFAULT_HOMING_SPEED
"""
def move_to(point, ground_speed = None, laser_on = False):

    if DUMMY_CONNECTIONS:
        return

    if CONNECT_KEITHLEY:
        if not laser_on:
            kh.set_output_off()
        else:
            kh.set_output_on()

    ground_speed = DEFAULT_HOME_SPEED if ground_speed is None else ground_speed


    # point data as a position (i.e., given invert, FsOR)
    global_point = local2globalmm(point)
    global_point_data = mm2lindata(global_point)

    dist = global_point - current_position()
    dist_data = mm2lindata(dist)

    veloc = abs(dist.unit) * ground_speed

    x_time = time_to_move(dist.x, veloc.x, LIN_STAGE_ACCELERATION)
    y_time = time_to_move(dist.y, veloc.y, LIN_STAGE_ACCELERATION)

    times = [x_time, y_time]
    last_to_move = times.index(max(times))

    if abs(dist_data.x) > 0:
        x_linear.set_target_speed(linspeed2lindata(veloc.x), await_reply = True)
    if abs(dist_data.y) > 0:
        y_linear.set_target_speed(linspeed2lindata(veloc.y), await_reply = True)

    # this is super ugly but it has to go like this procedurally, such that the
    #   command "await_reply"-ing (i.e., the slowest move) is the last one called
    if last_to_move == 0:
        if abs(dist_data.y) > 0:
            # don't await reply if x-axis will be slowest (necessary for
	    #   simultaneous moves)
            y_linear.move_abs(global_point_data.y)
        if abs(dist_data.x) > 0:
            x_linear.move_abs(global_point_data.x, await_reply = True)
    elif last_to_move == 1:
        if abs(dist_data.x) > 0:
            # don't await reply if y-axis will be slowest
            x_linear.move_abs(global_point_data.x)
        if abs(dist_data.y) > 0:
            y_linear.move_abs(global_point_data.y, await_reply = True)


    if CONNECT_KEITHLEY and laser_on:
        kh.set_output_off()


# OUTLINE THE GLOBAL REGION
# Draws an outline around the REGION_SIZE (ignoring LOCAL_O) in order to
#   test GLOBAL_O and TR boundaries, e.g., as determined in
#   POSITION_GETTER_MODE.
"""
z = stage height;  [z] = mm
[speed] = mm/s; if value == None, => DEFAULT_HOMING_SPEED
"""
def outline_region(z, speed = None):

    if DUMMY_CONNECTIONS:
        return

    move_to(V2((-0.1, -0.1)) + LOCAL_O * (-1 if INVERT_COORDINATES else 1))
    z_rotary.move_abs(mm2rotdata(z), await_reply = True)

    if CONNECT_KEITHLEY:
        kh.set_output_on()

    move_to(V2((-0.1, REGION_SIZE.y + 0.1)) + LOCAL_O * (-1 if INVERT_COORDINATES else 1), speed)
    move_to(REGION_SIZE + V2((0.1, 0.1)) + LOCAL_O * (-1 if INVERT_COORDINATES else 1), speed)
    move_to(V2((REGION_SIZE.x + 0.1, -0.1)) + LOCAL_O * (-1 if INVERT_COORDINATES else 1), speed)
    move_to(V2((-0.1, -0.1)) + LOCAL_O * (-1 if INVERT_COORDINATES else 1), speed)

    if CONNECT_KEITHLEY:
        kh.set_output_off()


# WIPE THE REGION
# Writes parallel lines that are separated by gap to be sufficiently
#   small such that write line edges overlap slightly (depending on
#   power and focal distance), in order to achieve bulk isotropy.
def wipe_region(z, gap = 0.08, speed = None):

    if DUMMY_CONNECTIONS:
        return

    move_to(V2((-1, 0)) + LOCAL_O * (-1 if INVERT_COORDINATES else 1))
    z_rotary.move_abs(mm2rotdata(z), await_reply = True)

    if CONNECT_KEITHLEY:
        kh.set_output_on()

    for i in range(int(REGION_SIZE.y / (2*gap)) + 1):
        if i > 0:
            move_to(V2((-1, gap * 2*i))                    + LOCAL_O * (-1 if INVERT_COORDINATES else 1), speed)
        move_to(V2((REGION_SIZE.x + 1, gap * 2*i))         + LOCAL_O * (-1 if INVERT_COORDINATES else 1), speed)
        move_to(V2((REGION_SIZE.x + 1, gap * (2*i + 1)))   + LOCAL_O * (-1 if INVERT_COORDINATES else 1), speed)
        move_to(V2((-1, gap * (2*i + 1)))                  + LOCAL_O * (-1 if INVERT_COORDINATES else 1), speed)

    if CONNECT_KEITHLEY:
        kh.set_output_off()


# HOME ALL
# Sends all stages back to their 'home' positions (x = y = z = 0)
def home_all():

    if DUMMY_CONNECTIONS:
        return

    # await_reply must = True for all homing commands, otherwise
    #   there'll be 'busy' errors because the succeeding commands will
    #   be called before homing is complete

    if CONNECT_ROTARY:
        z_rotary.home(await_reply = True)

    x_linear.home(await_reply = True)
    y_linear.home(await_reply = True)


""" CONVERSIONS """
# NOTE: ALWAYS int-cast when converting real units to data.
# NOTE: NEVER int-cast when converting data to a real unit.

# Converts distance (or V2) in mm to linear stage data
# Returns an int, or V2 of ints
def mm2lindata(mm):
    if type(mm) is V2:
        return (mm * DATA_PER_MM).round()
    return (int)(mm * DATA_PER_MM)

# Converts local position (V2, in mm) to global position (V2, in mm, OUT
#   OF CONTEXT of defined coordinate system), considering inversion, and
#   global and local frames of reference
# Returns V2 (mm)
def local2globalmm(local_mm):
    if (INVERT_COORDINATES):
        return TR + LOCAL_O + local_mm
    return GLOBAL_O - LOCAL_O - local_mm

# Converts linear speed (mm/s) to linear stage speed data (mstep/s)
# Returns an int
def linspeed2lindata(speed):
    return (int)(speed * DATA_PER_MM_SPEED)

# Converts linear stage distance data (mstep, or V2 of msteps) to
#   distance in mm, or V2 of mm
def lindata2mm(data):
    return data / DATA_PER_MM

# Converts an arbitrary measurement of focal distance ~ laser height
#   (mm) to degree-related rotary stage data (cf. B_EMPIR in
#   define_operating_constants, below)
# Returns an int
def mm2rotdata(mm):
    return deg2rotdata(B_EMPIR - DEG_PER_MM * mm)

# Converts rotary stage data to an arbitrary measurement of focal
#   distance ~ laser height (mm)
# Returns a float
def rotdata2mm(data):
    return (-rotdata2deg(data) + B_EMPIR) / DEG_PER_MM

# Converts rotation angle (degrees) to rotary stage data
# Returns an int
def deg2rotdata(deg):
    return (int)(deg * DATA_PER_DEG)

# Converts rotary stage data to rotation angle angle (degrees)
# Returns an float
def rotdata2deg(data):
    return data / DATA_PER_DEG

# Converts rotary stage speed (mm/s) to data
# Returns an int
def linspeed2rotdata(speed):
    return degspeed2rotdata(speed * DEG_PER_MM)

# Converts rotary stage speed (deg/s) to data
# Returns an int
def degspeed2rotdata(speed):
    return (int)(speed * DATA_PER_DEG_SPEED)


# TIME TO MOVE
#   Calculates the expected time it should take to make a given move,
#   based on distance, speed, and acceleration. This works well with x-
#   and y- stages, and although it could be made to work with the rotary
#   stage, you'd need to work in some additional conversion factors. Cf.
#   notes on units in README.md.
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


# CURRENT POSITION
# Polls x- and y- stages for their positions and returns a V2 object OUT
#   OF the context of the defined coordinate system (i.e., not
#   considering GLOBAL_O, autc.). It's used by print_position (for
#   POSITION_GETTER_MODE) and also by time_to_move (to calculate the
#   distance to a target position).
def current_position():
    if DUMMY_CONNECTIONS:
        return V2((0,0))
    return V2((lindata2mm(x_linear.get_position()), lindata2mm(y_linear.get_position())))

def print_position():
    # For some reason you have to poll position several times before
    #   it's properly updated, but this may be a TIME delay rather than
    #   a frequency delay...  more testing will tell.
    for i in range(15):
        current_position()
    print(current_position())


""" CONNECTIONS AND SETUP """

# SETUP KEITHLEY
# (Unless DUMMY_CONNECTIONS or !CONNECT_KEITHLEY):
# Opens a serial connection to the Keithley 2400 SourceMeter and sets
#   operating values that enable control of the connected Thorlabs SH05
#   beam shutter
def setup_keithley():
    global kh

    if DUMMY_CONNECTIONS or not CONNECT_KEITHLEY:
        return

    kh = kc.KeithleyHandler()

    kh.set_source_current(0.4)
    kh.set_voltage_compliance(21.0)
    kh.set_output_on()

# SETUP STAGES
# (Unless DUMMY_CONNECTIONS):
# Opens serial connections to Zaber stages and sets default operating
#   parameters, like target speed, acceleration, and max position, all
#   defined in define_operating_constants (below)
def setup_stages():
    global serial_conn, x_linear, y_linear, z_rotary

    if DUMMY_CONNECTIONS:
        return

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


# CLEAN UP
# (Unless !CONNECT_KEITHLEY):
# Turns off output of Keithley 2400 SourceMeter.
# (Unless DUMMY_CONNECTIONS):
# Homes stages and resets target speeds to default (in order to speed up
#   manual moves after programmed slower ones), then closes the serial
#   connection to the Zaber stages.
def clean_up():
    print("cleaning up")

    if DUMMY_CONNECTIONS:
    	print("nothing to clean up: DUMMY_CONNECTIONS = True")
    	return

    if CONNECT_KEITHLEY:
        kh.set_output_off()

    home_all()

    x_linear.set_target_speed(linspeed2lindata(DEFAULT_HOME_SPEED))
    y_linear.set_target_speed(linspeed2lindata(DEFAULT_HOME_SPEED))

    x_linear.enable_auto_reply()
    y_linear.enable_auto_reply()

    serial_conn.close()

    print("finished")


# DEFINE OPERATING CONSTANTS
# Sets global values, e.g., default speeds and accelerations, conversion
#   factors, and inversion parameter.
def define_operating_constants():

    """         ZABER CONTROL         """
    global GLOBAL_O, TR, LOCAL_O, REGION_SIZE, \
           STAGES_PORT, MM_PER_MSTEP, DATA_PER_MM, DATA_PER_MM_SPEED, DATA_PER_DEG, DATA_PER_DEG_SPEED, DEG_PER_MM, \
           DELTA_T, DEFAULT_HOME_SPEED, DEFAULT_ROT_SPEED, LIN_STAGE_ACCELERATION, ROT_STAGE_ACCELERATION, \
           ROTARY_MIN_ANGLE, ROTARY_MAX_ANGLE, B_EMPIR, INVERT_COORDINATES


    GLOBAL_O = V2((35.6, 39))		# ORIGIN = LASER FOCUSED ON BOTTOM LEFT CORNER
    TR = V2((21.6, 25))			# ...TOP RIGHT CORNER
    LOCAL_O = V2((0, 0))
    REGION_SIZE = GLOBAL_O - TR

    STAGES_PORT = "COM3"                # serial port to Zaber stages
    DATA_PER_MM = 1000 / 0.047625       # conversion from mm to data
    DATA_PER_MM_SPEED = 2240            # conversion from mm/s to data (speed)
    DATA_PER_DEG = 12800 / 3            # conversion from degrees to data
    DATA_PER_DEG_SPEED = 6990           # conversion from deg/s to data (speed)
    DEG_PER_MM = 9.2597                 # (deg/mm) empirical conversion, mm to degrees
    DELTA_T = 24                        # (ms) SET LOWER WHEN WRITING FASTER

    DEFAULT_HOME_SPEED = 5              # (mm/s)
    DEFAULT_ROT_SPEED = 15              # (deg/s)
    LIN_STAGE_ACCELERATION = 2000       # (data/s^2) ?

    # BE CAREFUL ABOUT INCREASING THIS VALUE! Cf. EXTREMELY IMPORTANT
    #   NOTES #3 in README.rm.
    ROT_STAGE_ACCELERATION = 40         # (data/s^2) ?

    ROTARY_MIN_ANGLE = 0.0	        # (deg) min position of rotary stage = upper bound on laser height
    ROTARY_MAX_ANGLE = 113.5	        # (deg) max postition of rotary stage = min. allowable laser height
    B_EMPIR = 1414.9692                 # (deg) position of rotary stage at 0 mm

    # True if writing to a sample to be viewed in microscope (since microscope inverts image)
    INVERT_COORDINATES = True;


if __name__ == '__main__':
    main()

