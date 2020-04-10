"""
DIRECTORY:	https://github.com/howwallace/howw-stage-controls.git
PROGRAM:	execute_commands.py
AUTHOR:		Harper O. W. Wallace
DATE:		9 Apr 2020

DESCRIPTION:
Executes move commands for Zaber Technologies rotary (1 x X-RSW60A) and
linear (2 x T-LSM050A) stages, all using binary encoding, and supervises
voltage and current control of Keithley 2400 SourceMeter to open and
close a beam shutter.

Parametrized move commands allow the user to write a single line, write
parallel lines, write part of a circle, write a full circle, wipe a
region, outline a region, and home all stages merely by specifying
relevant parameters (e.g., circle center, radius, and write speed); many
of these write functions are parametrized in several different ways in
order to simplify writing slight variations on the same type of pattern
(e.g., horizontal lines that span the entire sample region, v. vertical
lines that span a specified sub-region, v. diagonal lines that are
separated by a specified perpendicular distance). These commands and
their arguments are detailed very carefully below in this file.

A Cartesian coordinate system keeps track of sample boundaries and write
command positions within them (GLOBAL_O = "global origin," or the x- and
y- stage positions when the laser beam is focused on the bottom-left
corner of a square sample film; TR = "top right"); although GLOBAL_O is
defined as the "global origin," TR is another global origin, and is
often the more critical value to determine accurately, since it is ends
up defining the "bottom left" origin position relative to which moves
are made, when the coordinate system is inverted to account for
inversion under the microscope. The  This coordinate system will be more
useful and intuitive if it is specified for EACH film sample. To
facilitate determining these boundary positions for different samples, I
have designed (and installed, in our setup in Ebaugh Labs at Denison
University) a 3D-printable 1" glass microscope slide holder that can be
mounted to the T-LSM050A stage so that this coordinate system is
approximately (~0.01mm) conserved on removal and replacement of the
sample (cf. slide_holder.stl). I have also created a function that
allows the user to take manual control of the stages (using control
knobs on the stages themselves) to adjust their position until they
reach a desired position on the sample (e.g., GLOBAL_O or TR), at which
point the user can press the 'p' key on their keyboard to print the
position of the stages to the console, so they may be recorded, e.g., to
define GLOBAL_O and TR for a new sample. Another feature of the
coordinate system is that it can be sub-defined for a given write
command, without needing to redefine GLOBAL_O and/or TR, by specifying a
local origin (LOCAL_O), which is effectively a pointer vector from the
relevant global origin.

This coordinate system is measured in mm, but neither class of Zaber
stages uses this unit explicitly; instead, they use microsteps (which I
call "data" in conversion methods, because those values are what ends up
getting sent to the devices). Understanding how these units are
interconverted may resolve issues involving, which may arise; consult
[1] for a detailed explanation of Zaber's unit system.

An new and experimental feature is Mapping (cf. mapping_handler.py),
which will theoretically allow the user to simulate how write commands
will turn out in order to correct any errors before running them on a
sample; this will be particularly advantageous for writing multi-step
patterns that will be necessary to generate complex diffraction gratings
for Fourier projection and holographic images. This is not totally
finished yet, though.


EXTREMELY IMPORTANT NOTES:
1. DON'T LET THE OBJECTIVE LENS HIT THE SAMPLE HOLDER SCREWS.
Although it is possible to programmatically set a minimum height for the
rotary stage to alleviate concerns like this, unfortunately the screws
are sufficiently elevated above the sample that the focal distance would
probably be too large to write at modest power, if you were to try that
(rather than doing it that way, I've set the minimum position such that
the aluminum jacket for the objective lens will not collide with the
screws, so that the linear stages wouldn't be damaged in a collision).
Therefore it is EXTREMELY IMPORTANT that you move the stages such that
the objective lens is someplace within the sample region, THEN lower the
objective lens to the correct focal distance. This is done automatically
in the parametrized move commands defined below, but if you define any
more, or if you call move_to(...), then you must consider stage height.

2. DON'T MELT THE BEAM SHUTTER BY LEAVING THE LASER ON IT TOO LONG.
If the laser spot is on the shutter leaves for too long, they'll deform
and the device will no longer work. For the ThorLabs SH-05 beam shutter
we're using, about ten seconds is safe given the wavelength, spot size,
and highest throughput of our laser (according to a ThorLabs Application
Technician). This can be an inconvenience when you'd like to move around
the sample film without dragging an isotropic line behind you, e.g., and
so it means that you may have to find creative ways to organize writing
to minimize the time that the laser needs to be effectively "off";
alternatively, you may find that raising the objective lens sufficiently
high will diffuse the beam such that you can move the sample without
aligning/disaligning; as a last resort, you may need to TURN THE LASER
OFF MANUALLY in certain circumstances, rather than relying on the beam
shutter.

Communication with Zaber stages is achieved using a heavily modified
version of Zaber's Serial Library[2], and relies on /zaber/serial/*. I
would recommend just not doing anything to those files.

Communication and control over the Keithley is achieved using a module
published by T. Max Roberts[3], and relies on keithley_handler.py.

PLEASE CONSULT README.md FOR TROUBLESHOOTING AND REFERENCE INFORMATION.

LINKS:
[1] https://www.zaber.com/protocol-manual?protocol=Binary
[2] https://www.zaber.com/support/docs/api/core-python/0.6/ (available
      in this repo, with modifications, in zaber/serial/...)
[3] https://github.com/maxroberts/Keithley-2400-SourceMeter-Python-Int
      erface/blob/master/keithley_serial.py (link is broken, but the
      code is available in this repo in keithley_handler.py)
"""


# PARAMETERS FOR TESTING CONDITIONS
#   modify Keithley/stage connections for particular testing
#   circumstances e.g., don't bother moving the rotary if you're testing
#   movement in the plane DUMMY_CONNECTIONS effectively overrides
#   CONNECT_ROTARY and CONNECT_KEITHLEY e.g., D_C == True, these devices
#   won't connect even if C_R or C_K = True
# MAC_TESTING determines what modules are imported (OS limitations)


DUMMY_CONNECTIONS = True
CONNECT_ROTARY = False
CONNECT_KEITHLEY = False
MAC_TESTING = True


import sys, time, math
from mapping_handler import MappingHandler
from coordinates import V2, V3

# these modules are not available on mac
if not MAC_TESTING:
    import winsound
    import keyboard

if not DUMMY_CONNECTIONS:
    import keithley_handler as kc
    from zaber.serial import BinarySerial, BinaryDevice, BinaryCommand, CommandType


#"""
SAMPLE_NAME = "HW 2020-01-23 A"
GLOBAL_O = V2((35.6, 39.0260))      # ORIGIN = BOTTOM LEFT
TR = V2((21.6566, 25.0))            # TOP RIGHT
LOCAL_O = V2((6.2, 0.5))            # minor adjustments of writing region to prevent overlap without redefining global origin
#"""

"""
SAMPLE_NAME = "HW 2020-01-23 B"
GLOBAL_O = V2((35.9, 35.3))         # ORIGIN = BOTTOM LEFT
TR = V2((22.0, 21.0))               # TOP RIGHT
LOCAL_O = V2((1.0, 8.6))            # minor adjustments of writing region to prevent overlap without redefining global origin
#"""

"""
SAMPLE_NAME = "HW_1_19_1"
GLOBAL_O = V2((35.9859, 37.8388))   # ORIGIN = BOTTOM LEFT
TR = V2((21.5373, 25.3594))         # TOP RIGHT
LOCAL_O = V2((9.2, 0))              # minor adjustments of writing region to prevent overlap without redefining global origin
#"""
"""
SAMPLE_NAME = "HW_1_19_2"
GLOBAL_O = V2((34.9637, 38.2244))   # ORIGIN = BOTTOM LEFT
TR = V2((20.8351, 25.2664))         # TOP RIGHT
LOCAL_O = V2((12.5, 10))            # minor adjustments of writing region to prevent overlap without redefining global origin
#"""

REGION_SIZE = GLOBAL_O - TR



# POSITION_GETTER_MODE
#   allows you to move stages manually and press 'p' (on your keyboard)
#   to print out stage positions to the console. It's useful for
#   defining corners of sample regions: run execute_commands.py,
#   navigate to the sample origin using linear stage manual control
#   knobs, and press 'p' on the keyboard to print out their position.
#   Press 'esc' to exit.
# MOVE_MAPPING
#   allows you to visualize how commands will run before you put the
#   sample under the laser. True: then commands are given in a file
#   that corresponds to the sample of interest, which file keeps track
#   of historical read-write information so that the same commands can
#   be executedagain; False: then commands must be must bespecified
#   directly in this file


POSITION_GETTER_MODE = False
MOVE_MAPPING = True



def main():

    try:
        define_operating_constants()

        if CONNECT_KEITHLEY:
            setup_keithley()

        # be sure to call setup_stages() before moving/setting objective height
        # note that there's some give in the rotation of the pin through
	#   the microscope coarse control
        setup_stages()

        if POSITION_GETTER_MODE:

            # press 'p' to print current position to console
            keyboard.add_hotkey('p', print_position)
            # press 'esc' once you're finished with position-getting
            keyboard.wait('esc')

            print("copy to top of file:")

            # __TODO__:
            # print out the appropriate header information for the sample, w/ new origin, TR, etc.
            # draw outline, assuming that they've uploaded


        elif MOVE_MAPPING:

            mh = MappingHandler("/Users/harperwallace/Dropbox/GitHub/howw-stage-controls/samples/", SAMPLE_NAME, CONNECT_KEITHLEY, DEFAULT_HOME_SPEED)
            mh.draw_map()

            if mh.continue_to_run:
                write_commands()

        else:
            # MANUAL COMMAND-CALLING

            """ REFERENCE
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
            wipe_region(z, speed = None):
            move_to(point, ground_speed = None, laser_on = False):
            home_all():
            """


        if not MAC_TESTING:
            # make a little beep noise so I know it's all finished
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

    # __TODO__
    # parse some commands file that says what's going to happen

    #outline_region(142.0)

    #wipe_region(147.0, speed = 3)
    return



# write parallel lines with spaces: | | | |
# NOTE: start and end define ENDPOINTS OF THE FIRST LINE. Additional
#   lines will be written parallal, and approximately to the right,
#   depending on the exact angle between start and end, at a
#   perpendicular distance of gap.
def write_parallel_lines_gap(start, end, gap, speed, num_lines):

    direction = end - start

    # in order to write //-  as opposed to -// (perpendicular_cntclk)
    shift = direction.unit.perpendicular_clk * gap

    for i in range(num_lines):
        write_line(start + shift*i, end + shift*i, speed)


# write vertical parallel lines in an egyptian pattern: |-|_|-|_|
# NOTE: doesn't take num_lines as an argument.
# NOTE: unlike other parallel_lines functions, start and end define
#   REGION BOUNDARIES rather than ENDPOINTS OF THE FIRST LINE. This
#   means that vertical, parallel lines will be written in order to fill
#   a rectangle with bottom-left corner = start + LOCAL_O, top-right
#   corner = end + LOCAL_O.
def write_parallel_lines_vertical_continuous(z, start, end, gap, speed):

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

    # PRINT OUT WHERE TO SET LOCAL_O NEXT
    print(LOCAL_O + V2((0, abs((end - start).y) + gap)))
    print("OR")
    print(LOCAL_O + V2(((num_lines + 1)*gap, 0)))


# write horizontal parallel lines in a down->up egyptian pattern
# NOTE: doesn't take num_lines as an argument.
# NOTE: unlike other parallel_lines functions, start and end define REGION BOUNDARIES
#   rather than ENDPOINTS OF THE FIRST LINE.
def write_parallel_lines_horizontal_continuous(z, start, end, gap, speed):

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
    print(LOCAL_O + V2((0, (num_lines + 1)*gap)))
    print("OR")
    print(LOCAL_O + V2((abs((end - start).x) + gap, 0)))


# VERTICAL, REGION-TALL LINES
#   vertical lines that extend from LOCAL_O.y to LOCAL_O.y +
#   REGION_SIZE.y, with additional padding of 1 mm on each side. Two
#   such lines are written at each speed (mm/s) enumerated in speeds.
#   Inter-speed gap factor inflates the gap between same-speed line
#   pairs, so lines written at different speeds  can be more easily
#   distinguished and counted under the microscope. The laser stage
#   height adjusts according to z, *after* the linear stages move to
#   the starting position.
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
#   horizontal lines that extend from LOCAL_O.x to LOCAL_O.x +
#   REGION_SIZE.x, with additional padding of 1 mm on each side. Two
#   such lines are written at each speed (mm/s) enumerated in speeds.
#   Inter-speed gap factor inflates the gap between same-speed line
#   pairs, so lines written at different speeds  can be more easily
#   distinguished and counted under the microscope. The laser stage
#   height adjusts according to z, *after* the linear stages move to
#   the starting position.
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
#   horizontal lines that extend from LOCAL_O.x to LOCAL_O.x +
#   REGION_SIZE.x, with additional padding of 1 mm on each side. Two
#   such lines are written at each speed (mm/s) enumerated in speeds.
#   Inter-speed gap factor inflates the gap between same-speed line
#   pairs, so lines written at different speeds  can be more easily
#   distinguished and counted under the microscope. The laser stage
#   height adjusts according to z, *after* the linear stages move to
#   the starting position.
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


# WRITE PARALLEL LINES WITH A SPEED INCREMENT
#   writes parallel lines at different speeds, starting at speed and
#   increasing by delta_speed for every num_lines_per_speed lines
#   written at that temporary speed. num_speeds determines how many
#   times this outer loop iterates, and hence how many total lines are
#   written = num_lines_per_speed * num_speeds
# NOTE: start and end define ENDPOINTS OF THE FIRST LINE. Additional
#   lines will be written parallal, and approximately to the right,
#   depending on the exact angle between start and end, at a
#   perpendicular distance of gap.
def write_parallel_lines_delta_s(start, end, gap, speed, delta_speed, num_lines_per_speed, num_speeds):

    for i in range(num_speeds):
        spacer = (num_lines_per_speed + (0.7 if num_lines_per_speed > 1 else 0)) * i * gap
        write_parallel_lines(start + spacer, end + spacer, gap, speed + i*delta_speed, num_lines_per_speed)

# WRITE LINE
def write_line(start, end, speed):

    move_to(start)
    move_to(end, ground_speed = speed, laser_on = True)


def write_circle(center, radius, speed):

    write_part_circle(center, radius, 0, 360, speed)

"""
[start], [end] = deg
"""
def write_part_circle(center, radius, start_deg, end_deg, speed):

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


# [point] = V2 or V3, in mm
# ground_speed does not include the speed of changing z; (mm/s)
# NOTE: MOVES ONLY IN PLANE, AS WRITTEN, BUT MIGHT REASONABLY BE
#   **UPDATED** TO MOVE ROTARY TOO
def move_to(point, ground_speed = None, laser_on = False):

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
    # extract x, y components of the distance
    lin_dist = V2(dist)
    lin_dist_data = mm2lindata(lin_dist)

    veloc = abs(lin_dist.unit) * ground_speed

    x_time = time_to_move(lin_dist.x, veloc.x, LIN_STAGE_ACCELERATION)
    y_time = time_to_move(lin_dist.y, veloc.y, LIN_STAGE_ACCELERATION)

    times = [x_time, y_time]
    last_to_move = times.index(max(times))

    if abs(lin_dist_data.x) > 0:
        x_linear.set_target_speed(linspeed2lindata(veloc.x), await_reply = True)
    if abs(lin_dist_data.y) > 0:
        y_linear.set_target_speed(linspeed2lindata(veloc.y), await_reply = True)

    # this is super ugly but it has to go like this procedurally, such that the
    #   command "await_reply"-ing (i.e., the slowest move) is the last one called
    if last_to_move == 0:
        if abs(lin_dist_data.y) > 0:
            # don't await reply if x-axis will be slowest (necessary for
	    #   simultaneous moves)
            y_linear.move_abs(global_point_data.y)
        if abs(lin_dist_data.x) > 0:
            x_linear.move_abs(global_point_data.x, await_reply = True)
    elif last_to_move == 1:
        if abs(lin_dist_data.x) > 0:
            # don't await reply if y-axis will be slowest
            x_linear.move_abs(global_point_data.x)
        if abs(lin_dist_data.y) > 0:
            y_linear.move_abs(global_point_data.y, await_reply = True)


    if CONNECT_KEITHLEY and laser_on:
        kh.set_output_off()


# z = stage height;  [z] = mm
# assumes speed = DEFAULT_HOME_SPEED if not specified
# draws an outline around the REGION_SIZE (ignoring LOCAL_O) in order to
#   test GLOBAL_O and TR boundaries, e.g., as determined in
#   POSITION_GETTER_MODE.
def outline_region(z, speed = None):

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


# writes parallel lines that are separated by WIPE_GAP, which is defined
#   in define_operating_constants to be sufficiently small such that
#   write line edges overlap slightly (depending on power and focal
#   distance), in order to achieve bulk isotropy.
def wipe_region(z, speed = None):

    move_to(V2((-1, 0)) + LOCAL_O * (-1 if INVERT_COORDINATES else 1))
    z_rotary.move_abs(mm2rotdata(z), await_reply = True)

    if CONNECT_KEITHLEY:
        kh.set_output_on()

    for i in range(int(REGION_SIZE.y / (2*WIPE_GAP)) + 1):
        if i > 0:
            move_to(V2((-1, WIPE_GAP * 2*i))                    + LOCAL_O * (-1 if INVERT_COORDINATES else 1), speed)
        move_to(V2((REGION_SIZE.x + 1, WIPE_GAP * 2*i))         + LOCAL_O * (-1 if INVERT_COORDINATES else 1), speed)
        move_to(V2((REGION_SIZE.x + 1, WIPE_GAP * (2*i + 1)))   + LOCAL_O * (-1 if INVERT_COORDINATES else 1), speed)
        move_to(V2((-1, WIPE_GAP * (2*i + 1)))                  + LOCAL_O * (-1 if INVERT_COORDINATES else 1), speed)

    if CONNECT_KEITHLEY:
        kh.set_output_off()



# sends all stages back to their 'home' positions (x = y = z = 0)
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
#   considering inversion / global and local frames of reference
# returns a V2 of integers (linear stage data)
def local2globalmm(local_mm):
    if (INVERT_COORDINATES):
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
    if DUMMY_CONNECTIONS:
        return V2((0,0))
    if CONNECT_ROTARY:
        return V3((lindata2mm(x_linear.get_position()), lindata2mm(y_linear.get_position()), rotdata2mm(z_rotary.get_position())))
    return V2((lindata2mm(x_linear.get_position()), lindata2mm(y_linear.get_position())))


def print_position():
    # for some reason you have to poll position several times before
    #   it's properly updated, but this may be a TIME delay rather than
    #   a frequency delay...  more testing will tell
    for i in range(15):
        current_position()
    print(current_position())


""" CONNECTIONS AND SETUP """

def setup_keithley():
    global kh

    kh = kc.KeithleyHandler()

    kh.set_source_current(0.4)
    kh.set_voltage_compliance(21.0)
    kh.set_output_on()


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


def define_operating_constants():

    """         ZABER CONTROL         """
    global STAGES_PORT, MM_PER_MSTEP, DATA_PER_MM, DATA_PER_MM_SPEED, DATA_PER_DEG, DATA_PER_DEG_SPEED, DEG_PER_MM, \
           DELTA_T, DEFAULT_HOME_SPEED, DEFAULT_ROT_SPEED, LIN_STAGE_ACCELERATION, ROT_STAGE_ACCELERATION, WIPE_GAP, \
           ROTARY_MIN_ANGLE, ROTARY_MAX_ANGLE, B_EMPIR, INVERT_COORDINATES

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
    ROT_STAGE_ACCELERATION = 40         # (data/s^2) ?

    WIPE_GAP = 0.08        	        # (mm) depends on focal distance and power

    ROTARY_MIN_ANGLE = 0.0	        # (deg) min position of rotary stage = upper bound on laser height
    ROTARY_MAX_ANGLE = 113.5	        # (deg) max postition of rotary stage = min. allowable laser height
    B_EMPIR = 1414.9692                 # (deg) position of rotary stage at 0 mm

    # True if writing to a sample to be viewed in microscope (since microscope inverts image)
    INVERT_COORDINATES = True;


if __name__ == '__main__':
    main()

