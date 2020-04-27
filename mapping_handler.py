"""
DIRECTORY:	https://github.com/howwallace/howw-stage-controls.git
PROGRAM:	mapping_handler.py
AUTHOR:		Harper O. W. Wallace
DATE:		9 Apr 2020

DESCRIPTION:
Mapping predicts how moves will track before actual laser-writing, so
paths can be verified before a sample is altered, so the time it will
take to write these paths can be estimated before writing, and also so
that the user can keep track of the paths they've written to a sample in
the past (path renderings can be saved as .jpgs using the "Save" button
at the bottom of the gui).

I have not had the opportunity to test this portion of the library
together with execute_commands.py on the actual setup (since labwork and
University operations were suspended in response to COVID-19), which
means that paths predicted here may vary from those that are actually
followed; in particular, I am uncertain about the angular direction the
stages move when tracing a circle. Thankfully, verifying these predicted
paths should only entail writing a series of commands to an actual
sample and comparing the written pattern to the predicted one; if there
are discrepancies, I'd recommend updating the code (below) that renders
the prediction, rather than the code that actually writes to the samples.
"""


import numpy as np
import math
import re
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.lines as mlines
from matplotlib.widgets import Button

from matplotlib.patches import Rectangle, Circle, Arc
from coordinates import V2

from datetime import datetime
from pytz import timezone



class MappingHandler(object):
    
    def __init__(self, path_prefix, sample_name, connect_keithley, default_speed):

        self.path_prefix = path_prefix
        self.sample_name = sample_name

        # If True, assumes that the beam shutter will close for moves
        #   between (and hence won't render those moves, but will
        #   consider and the paths between moves anyway, as gray,
        #   dashed lines)
	
        self.connect_keithley = connect_keithley

        self.default_speed = default_speed
        
        self.TR = V2((0, 0))
        self.GLOBAL_O = V2((0, 0))
        self.REGION_SIZE = V2((0, 0))
        self.local_o = V2((0, 0))
        self.curr_pos = V2((0, 0))
        self.new_file_text = ""
        self.new_cmds_array = []
        self.continue_to_run = False

    def draw_map(self):
        fix, ax = plt.subplots(nrows=1, ncols=1, figsize=(5.5,6))
        plt.subplots_adjust(bottom=0.2)

        axbcancel = plt.axes([0.7, 0.05, 0.1, 0.075])
        bcancel = Button(axbcancel, 'Cancel')
        bcancel.on_clicked(self.cancel)
        
        axbrun = plt.axes([0.81, 0.05, 0.1, 0.075])
        brun = Button(axbrun, 'Run')
        brun.on_clicked(self.run)

        try:
            total_time = 0
            curr_command = 0
            in_new_cmds = False
            
            log_file = open(self.path_prefix + self.sample_name + ".txt", "r")
            
            for line in log_file.readlines():

                if len(line.rstrip()) > 0 and line[0] != "#":

                    step_time = 0
                    stripped_line = line.split("#")[0].rstrip()

                    # setting GLOBAL_O, TR, or LOCAL_O
                    if stripped_line.find("=") != -1 and stripped_line.find("=") < stripped_line.find("("):
                        
                        val = stripped_line.split("=",1)[0].rstrip()                        
                        args = list(map(float, re.sub("[^0-9.,]","", stripped_line.split("=",1)[1].replace("V2","").replace("V3","")).split(",")))

                        if val == "GLOBAL_O":
                            self.GLOBAL_O = V2((args[0], args[1]))
                        elif val == "TR":
                            self.TR = V2((args[0], args[1]))
                            self.REGION_SIZE = self.GLOBAL_O - self.TR
                            ax.add_patch(Rectangle((0, 0), self.REGION_SIZE.x, self.REGION_SIZE.y, fill=None, alpha=1))
                            plt.xlim(left = - 0.05 * self.REGION_SIZE.x, right = 1.05 * self.REGION_SIZE.x)
                            plt.ylim(bottom = - 0.05 * self.REGION_SIZE.y, top = 1.05 * self.REGION_SIZE.y)
                            ax.xaxis.set_ticks(np.arange(0,self.REGION_SIZE.x,2))
                            ax.yaxis.set_ticks(np.arange(0,self.REGION_SIZE.y,2))
                            ax.set_aspect('equal', adjustable='box')
                        elif val == "LOCAL_O":
                            self.local_o = V2((args[0], args[1]))

                        self.new_file_text += line

                    # calling command
                    else:
                        
                        curr_command += 1
                        
                        cmd = stripped_line.split("(",1)[0]
                        
                        # separates out arguments, omitting lists (e.g., "speeds" array in write_parallel_lines_vertical_region_tall)

                        args_str = stripped_line.split("(",1)[1].replace("V2","").replace("V3","")
                        array_arg = re.search("\[.*?\]", args_str)
                        
                        if array_arg:
                            speeds = list(map(float, re.sub("\[|\]", "", array_arg.group(0)).split(",")))
                            args_str = re.sub("\[.*?\]", "{}".format(len(speeds)), args_str)
                        args = list(map(float, re.sub("[^0-9.,-]", "", args_str).split(",")))


                        
                        # write_parallel_lines_vertical_continuous(z, start, end, gap, speed)
                        if cmd == "write_parallel_lines_vertical_continuous":
                            start = self.local_o + V2((args[1], args[2]))
                            end = self.local_o + V2((args[3], args[4]))
                            gap = args[5]
                            shift = V2((gap, 0))
                            speed = args[6]
                            ax.annotate(curr_command, xy=(start.x, start.y))

                            num_lines = int(abs((end - start).x)/float(shift.x))
                            for i in range(0, num_lines, 2):
                                step_time += self.render_write_line(ax, start + shift*i, V2((start.x, end.y)) + shift*i, speed, in_new_cmds)
                                step_time += self.render_write_line(ax, V2((start.x, end.y)) + shift*(i + 1), start + shift*(i + 1), speed, in_new_cmds)

                            if in_new_cmds:
                                self.new_cmds_array.append((cmd, args[0], start, end, gap, speed))

    
                        # write_parallel_lines_horizontal_continuous(z, start, end, gap, speed)
                        elif cmd == "write_parallel_lines_horizontal_continuous":
                            start = self.local_o + V2((args[1], args[2]))
                            end = self.local_o + V2((args[3], args[4]))
                            gap = args[5]
                            speed = args[6]
                            shift = V2((0, gap))
                            ax.annotate(curr_command, xy=(start.x, start.y))

                            num_lines = int(abs((end - start).y)/float(shift.y))
                            for i in range(0, num_lines, 2):
                                step_time += self.render_write_line(ax, start + shift*i, V2((end.x, start.y)) + shift*i, speed, in_new_cmds)
                                step_time += self.render_write_line(ax, V2((end.x, start.y)) + shift*(i + 1), start + shift*(i + 1), speed, in_new_cmds)

                            if in_new_cmds:
                                self.new_cmds_array.append((cmd, args[0], start, end, gap, speed))

    
                        # write_parallel_lines_vertical_region_tall(z, speeds, gap, inter_speed_gap_factor = 0.2)
                        elif cmd == "write_parallel_lines_vertical_region_tall":

                            start = self.local_o + V2((0, -1))
                            end = self.local_o + V2((0, self.REGION_SIZE.y + 1))
                            gap = args[2]
                            inter_speed_gap_factor = 0.2 if len(args) < 4 else args[3]
                            shift = V2(((2 + inter_speed_gap_factor)*gap, 0))

                            ax.annotate(curr_command, xy=(start.x, start.y))
                            for i in range(len(speeds)):
                                speed = speeds[i]

                                step_time += self.render_write_line(ax, start + shift*i, end + shift*i, speed, in_new_cmds)
                                step_time += self.render_write_line(ax, end + shift*i + V2((gap, 0)), start + shift*i + V2((gap, 0)), speed, in_new_cmds)

                            if in_new_cmds:
                                self.new_cmds_array.append((cmd, args[0], speeds, gap, inter_speed_gap_factor))

    
                        # write_parallel_lines_horizontal_region_wide(z, speeds, gap, inter_speed_gap_factor = 0.2)
                        elif cmd == "write_parallel_lines_horizontal_region_wide":

                            start = self.local_o + V2((-1, 0))
                            end = self.local_o + V2((self.REGION_SIZE.x + 1, 0))
                            gap = args[2]
                            inter_speed_gap_factor = 0.2 if len(args) < 4 else args[3]
                            shift = V2((0, (2 + inter_speed_gap_factor)*gap))

                            ax.annotate(curr_command, xy=(start.x, start.y))
                            for i in range(len(speeds)):
                                speed = speeds[i]

                                step_time += self.render_write_line(ax, start + shift*i, end + shift*i, speed, in_new_cmds)
                                step_time += self.render_write_line(ax, end + shift*i + V2((0, gap)), start + shift*i + V2((0, gap)), speed, in_new_cmds)

                            if in_new_cmds:
                                self.new_cmds_array.append((cmd, args[0], speeds, gap, inter_speed_gap_factor))

    
                        # write_parallel_lines_horizontal_const_height(z, x_width, speeds, gap, inter_speed_gap_factor = 0.2)
                        elif cmd == "write_parallel_lines_horizontal_const_height":

                            x_width = args[1]
                            start = self.local_o
                            end = self.local_o + V2((x_width, 0))
                            gap = args[3]
                            inter_speed_gap_factor = 0.2 if len(args) < 5 else args[4]
                            shift = V2((0, (2 + inter_speed_gap_factor)*gap))

                            ax.annotate(curr_command, xy=(start.x, start.y))
                            for i in range(len(speeds)):
                                speed = speeds[i]

                                step_time += self.render_write_line(ax, start + shift*i, end + shift*i, speed, in_new_cmds)
                                step_time += self.render_write_line(ax, end + shift*i + V2((0, gap)), start + shift*i + V2((0, gap)), speed, in_new_cmds)

                            if in_new_cmds:
                                self.new_cmds_array.append((cmd, args[0], x_width, speeds, gap, inter_speed_gap_factor))


                        # write_parallel_lines_gap(z, start, end, gap, speed, num_lines)
                        elif cmd == "write_parallel_lines_gap":
                            
                            start = self.local_o + V2((args[1], args[2]))
                            end = self.local_o + V2((args[3], args[4]))
                            gap = args[5]
                            speed = args[6]
                            num_lines = int(args[7])
                            ax.annotate(curr_command, xy=(start.x, start.y))
                            
                            direction = end - start
                            shift = direction.unit.perpendicular_clk * gap
                            for i in range(num_lines):
                                step_time += self.render_write_line(ax, start + shift*i, end + shift*i, speed, in_new_cmds)

                            if in_new_cmds:
                                self.new_cmds_array.append((cmd, args[0], start, end, gap, speed, num_lines))

                        # write_parallel_lines_delta_s(z, start, end, gap_dist, speed, delta_speed, num_lines_per_speed, num_speeds)
                        elif cmd == "write_parallel_lines_delta_s":
                            
                            start = self.local_o + V2((args[1], args[2]))
                            end = self.local_o + V2((args[3], args[4]))
                            gap_dist = args[5]
                            speed = args[6]
                            delta_speed = args[7]
                            num_lines_per_speed = int(args[8])
                            num_speeds = int(args[9])
                            ax.annotate(curr_command, xy=(start.x, start.y))
                            
                            direction = end - start
                            shift = direction.unit.perpendicular_clk * gap_dist
                            inter_speed_spacer = shift * (num_lines_per_speed + (0.7 if num_lines_per_speed > 1 else 0))
                            for i in range(num_speeds):

                                for j in range(num_lines_per_speed):
                                    step_time += self.render_write_line(ax, start + inter_speed_spacer*i + shift*j, end + inter_speed_spacer*i + shift*j, speed + i*delta_speed, in_new_cmds)

                            if in_new_cmds:
                                self.new_cmds_array.append((cmd, args[0], start, end, gap_dist, speed, delta_speed, num_lines_per_speed, num_speeds))

    
                        # write_line(start, end, speed)
                        elif cmd == "write_line":
                            
                            start = self.local_o + V2((args[0], args[1]))
                            end = self.local_o + V2((args[2], args[3]))
                            speed = args[4]

                            ax.annotate(curr_command, xy=(start.x, start.y))
                            step_time += self.render_write_line(ax, start, end, speed, in_new_cmds)

                            if in_new_cmds:
                                self.new_cmds_array.append((cmd, start, end, speed))

    
                        # write_circle(center, radius, speed)
                        elif cmd == "write_circle":
                            
                            center = self.local_o + V2((args[0], args[1]))
                            radius = args[2]
                            speed = args[3]
                            color = '#DF8800' if in_new_cmds else '#149E27'
                            
                            start = V2((center.x + radius, center.y))
                            ax.annotate(curr_command, xy=(start.x, start.y))     #args[-1][2:], xy=(start.x, start.y))
                            ax.add_patch(Circle((center.x, center.y), radius = radius, fill=None, alpha=1, color=color, linewidth=1.5))

                            if in_new_cmds:
                                step_time += self.render_move_to_start(ax, start) + 2*np.pi*radius / speed
                                self.new_cmds_array.append((cmd, center, radius, speed))

                            self.curr_pos.setXY(start)

    
                        # write_part_circle(center, radius, start_deg, end_deg, speed)
                        elif cmd == "write_part_circle":
                            
                            center = self.local_o + V2((args[0], args[1]))
                            radius = args[2]
                            start_deg = args[3]
                            end_deg = args[4]
                            speed = args[5]
                            color = '#DF8800' if in_new_cmds else '#149E27'
                            
                            start = center + V2(start_deg)*radius
                            ax.annotate(curr_command, xy=(start.x, start.y))     #args[-1][2:], xy=(start.x, start.y))
                            ax.add_patch(Arc((center.x, center.y), 2*radius, 2*radius, 0, start_deg, end_deg, fill=None, alpha=1, color=color, linewidth=1.5))
                           
                            if in_new_cmds:
                                step_time += self.render_move_to_start(ax, start) + 2*np.pi*(end_deg - start_deg)*radius / (360*speed)
                                self.new_cmds_array.append((cmd, center, radius, start_deg, end_deg, speed))

                            self.curr_pos.setXY(center + V2(end_deg)*radius)


                        # outline_region(z, speed = None)
                        # DON'T CORRECT FOR LOCAL_O
                        elif cmd == "outline_region":
                            
                            speed = self.default_speed if len(args) < 2 else args[1]

                            ax.annotate(curr_command, xy=(-0.1, -0.1))
                            step_time += self.render_write_line(ax, V2((-0.1,-0.1)), V2((-0.1, self.REGION_SIZE.y + 0.1)), speed, in_new_cmds)
                            step_time += self.render_write_line(ax, V2((-0.1, self.REGION_SIZE.y + 0.1)), self.REGION_SIZE + V2((0.1, 0.1)), speed, in_new_cmds)
                            step_time += self.render_write_line(ax, self.REGION_SIZE + V2((0.1, 0.1)), V2((self.REGION_SIZE.x + 0.1, -0.1)), speed, in_new_cmds)
                            step_time += self.render_write_line(ax, V2((self.REGION_SIZE.x + 0.1, -0.1)), V2((-0.1,-0.1)), speed, in_new_cmds)

                            if in_new_cmds:
                                self.new_cmds_array.append((cmd, args[0], speed))


                        # wipe_region(z, gap = 0.08, speed = None)
                        # DON'T CORRECT FOR LOCAL_O
                        elif cmd == "wipe_region":
                            
                            gap = args[1]
                            speed = self.default_speed if len(args) < 3 else args[2]

                            for i in range(int(self.REGION_SIZE.y / (2*gap)) + 1):
                                step_time += self.render_write_line(ax, V2((-1, gap * 2*i)), V2((self.REGION_SIZE.x + 1, gap * 2*i)), speed, in_new_cmds)
                                step_time += self.render_write_line(ax, V2((self.REGION_SIZE.x + 1, gap * (2*i + 1))), V2((-1, gap * (2*i + 1))), speed, in_new_cmds)
                        
                            if in_new_cmds:
                                self.new_cmds_array.append((cmd, args[0], gap, speed))

                        
                        # move_to(point, ground_speed = None, laser_on = False)
                        elif cmd == "move_to":
                                         
                            if in_new_cmds:
                                point = self.local_o + V2((args[0], args[1]))
                                speed = self.default_speed if len(args) < 3 else args[2]

                                ax.annotate(curr_command, xy=(self.curr_pos.x, self.curr_pos.y))
                                step_time += self.render_move_to_start(ax, point, speed)
                                self.new_cmds_array.append((cmd, point, speed))

                        
                        if in_new_cmds:
                            total_time += step_time
                            self.new_file_text += line.rstrip() + "\t\t# [{}]\n".format(curr_command)
                        else:
                            self.new_file_text += line

                # reset local origin for new commands
                # NOTE: don't change the ## NEW header in the template sample file
                elif line[0:6] == "## NEW":
                    
                    in_new_cmds = True

                    self.new_file_text = self.new_file_text.rstrip() + "\n\n# " + datetime.now(timezone("US/Eastern")).strftime("%Y-%m-%d %H:%M:%S") + "\n"
                    self.new_file_text += "LOCAL_O = V2((0, 0))\n"
                    self.local_o = V2((0, 0))
                    self.curr_pos = self.TR*(-1)
                    
                    #curr_power = 0

                elif line[0:6] == "## REF":
                    
                    in_new_cmds = False
                    self.new_file_text += "\n\n\n\n## NEW COMMANDS\n\n\n\n\n\n" + line

                # include newlines and comments
                elif line[0] == "#" or not in_new_cmds:
                    self.new_file_text += line


            log_file.close()
            
            plt.text(-110.0, 3.0, "{} s = {} min".format(int(10*total_time)/10.0, int(100*total_time/60.0)/100.0), fontsize=12)
            plt.show()
    
        except FileNotFoundError:
            print("{}{} not found.".format(self.path_prefix, self.sample_name))


    def run(self, event):
        plt.close()
        self.continue_to_run = True


    def cancel(self, event):
        plt.close()
        self.continue_to_run = False


    # returns the duration of the write
    def render_write_line(self, ax, start, end, speed, is_new):

        t = 0
        color = '#DF8800' if is_new else '#149E27'        # i.e., orange if new;  else green
        
        if is_new:
            t += self.render_move_to_start(ax, start)
        
        l = mlines.Line2D([start.x, end.x], [start.y, end.y], color=color)
        ax.add_line(l)
        self.curr_pos.setXY(end)
        return t + (end - start.asV2()).magnitude / speed

    def render_move_to_start(self, ax, start, speed = None):
        
        if speed == None:
            speed = self.default_speed
        
        if start != self.curr_pos.asV2():       # then at least calculate the time to move to start
            if (not self.connect_keithley):          # then map move to start
                l = mlines.Line2D([self.curr_pos.x, start.x], [self.curr_pos.y, start.y], linestyle=':', color='lightgray')
                ax.add_line(l)
            dist = (start - self.curr_pos.asV2()).magnitude
            self.curr_pos.setXY(start)
            return dist / speed
        return 0

    def update_sample_history(self):
        log_file = open(self.path_prefix + self.sample_name + ".txt", "w")
        log_file.write(self.new_file_text)
        log_file.close()


