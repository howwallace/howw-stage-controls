import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.lines as mlines
from matplotlib.widgets import Button

from matplotlib.patches import Rectangle, Circle
from coordinates import V2, V3

from datetime import datetime
from pytz import timezone


class MoveMapper(object):
    
    def __init__(self, sample_name, connect_keithley, default_speed):
        self.connect_keithley = connect_keithley
        self.default_speed = default_speed
        
        self.sample_name = sample_name
        self.TR = V2((0, 0))
        self.GLOBAL_O = V2((0, 0))
        self.REGION_SIZE = V2((0, 0))
        self.local_o = V2((0, 0))
        self.curr_pos = V3((0, 0, 0))        # should probably adjust so initial z is home height
        self.reformatted_file_text = ""
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
            curr_command = 1
            curr_power = 0
            new_commands_section = False
            reformatted_new_cmds = ""
            
            log_file = open(PATH_PREFIX + self.sample_name + ".txt", "r")
            for line in log_file.readlines():
                if (line[0] != "#") and (line[0] != "-"):
                    stripped_line = line.split("#")[0].rstrip()
                    args = stripped_line.split("\t")
                    step_time = 0
                    reformatted_str = ""
                    color = '#DF8800' if new_commands_section else '#149E27'        # i.e., orange if new;  else green
                    
                    if args[0] == "L":
                        start = self.local_o + V2(args[1])
                        end = self.local_o + V2(args[2])
                        speed = float(args[3])
                        ax.annotate(curr_command, xy=(start.x, start.y))     #args[-1][2:], xy=(start.x, start.y))
                        step_time = self.render_write_line(ax, start, end, speed, color)
                        curr_command += 1
                    elif args[0] == "PLH":
                        start = self.local_o + V2(args[1])
                        end = self.local_o + V2(args[2])
                        gap = float(args[3])
                        speed = float(args[4])
                        ax.annotate(curr_command, xy=(start.x, start.y))     #args[-1][2:], xy=(start.x, start.y))
                        for i in range(int((end - start).y / (2*gap)) + 1):
                            step_time += self.render_write_line(ax, start + V2((0, 2*i*gap)), V2((end.x, start.y)) + V2((0, 2*i*gap)), speed, color)
                            step_time += self.render_write_line(ax, V2((end.x, start.y)) + V2((0, (2*i + 1)*gap)), start + V2((0, (2*i + 1)*gap)), speed, color)
                        curr_command += 1
                    elif args[0] == "PLV":
                        start = self.local_o + V2(args[1])
                        end = self.local_o + V2(args[2])
                        gap = float(args[3])
                        speed = float(args[4])
                        ax.annotate(curr_command, xy=(start.x, start.y))     #args[-1][2:], xy=(start.x, start.y))
                        for i in range(int((end - start).x / (2*gap)) + 1):
                            step_time += self.render_write_line(ax, V2((start.x + 2*i*gap, start.y)), V2((start.x + 2*i*gap, end.y)), speed, color)
                            step_time += self.render_write_line(ax, V2((start.x + (2*i + 1)*gap, end.y)), V2((start.x + (2*i + 1)*gap, start.y)), speed, color)
                        curr_command += 1
                    elif args[0] == "C":
                        center = self.local_o + V2(args[1])
                        radius = float(args[2])
                        speed = float(args[3])
                        start = V2((center.x + radius, center.y))
                        ax.annotate(curr_command, xy=(start.x, start.y))     #args[-1][2:], xy=(start.x, start.y))
                        ax.add_patch(Circle((center.x, center.y), radius = radius, fill=None, alpha=1, color=color, linewidth=1.5))
                        step_time = self.render_move_to_start(ax, start) + 2*np.pi*radius / speed
                        self.curr_pos.setXY(start)
                        curr_command += 1
                    # wipe functions ignore local_o
                    elif args[0] == "WH":
                        gap = float(args[1])
                        speed = float(args[2])
                        ax.annotate(curr_command, xy=(0, 0))     #args[-1][2:], xy=(start.x, start.y))
                        for i in range(int(REGION_SIZE.y / (2*gap)) + 1):
                            step_time += self.render_write_line(ax, V2((-0.5, 2*i*gap)), V2((self.REGION_SIZE.x + 0.5, 2*i*gap)), speed, color)
                            step_time += self.render_write_line(ax, V2((self.REGION_SIZE.x + 0.5, (2*i + 1)*gap)), V2((-0.5, (2*i + 1)*gap)), speed, color)
                        curr_command += 1
                    elif args[0] == "WV":
                        gap = float(args[1])
                        speed = float(args[2])
                        ax.annotate(curr_command, xy=(0, 0))     #args[-1][2:], xy=(start.x, start.y))
                        for i in range(int((end - start).x / (2*gap)) + 1):
                            step_time += self.render_write_line(ax, V2((2*i*gap, -0.5)), V2((2*i*gap, self.REGION_SIZE.y + 0.5)), speed, color)
                            step_time += self.render_write_line(ax, V2(((2*i + 1)*gap, self.REGION_SIZE.y + 0.5)), V2(((2*i + 1)*gap, -0.5)), speed, color)
                        curr_command += 1
                    
                    
                    # reformat new commands with comment to the side to keep track of power/height settings
                    if new_commands_section and stripped_line != "":
                        if args[0] not in ["P", "Z", "LOC"]:
                            total_time += step_time

                            curr_power_str = " ----" if curr_power == 0 else " "*(2 - int(math.log10(curr_power))) + str(curr_power)
                            reformatted_cmd = stripped_line + "\t"*int(9 - len(stripped_line.expandtabs())/8) + "## {}. {}(z = {},  P = {} mW,  t = {} s {}= {} min)\n".format(curr_command - 1, " "*(1 - int(math.log10(curr_command - 1))) + args[0] + " "*(4 - len(args[0])), self.curr_pos.z, curr_power_str, int(step_time), " "*(1 - int(step_time/10)), int(step_time/60 + 0.5))
                            reformatted_new_cmds += reformatted_cmd
                        elif args[0] != "LOC":
                            reformatted_new_cmds += line
                            self.reformatted_file_text += line
                        else:
                            reformatted_new_cmds += line
                    else:
                        self.reformatted_file_text += line
        
        
                    if args[0] == "TR":
                        self.TR = V2(args[1])    # string parsing added in coordinates
                    elif args[0] == "O":
                        self.GLOBAL_O = V2(args[1])
                        self.REGION_SIZE = self.GLOBAL_O - self.TR
                        ax.add_patch(Rectangle((0, 0), self.REGION_SIZE.x, self.REGION_SIZE.y, fill=None, alpha=1))
                        plt.xlim(left = - 0.05 * self.REGION_SIZE.x, right = 1.05 * self.REGION_SIZE.x)
                        plt.ylim(bottom = - 0.05 * self.REGION_SIZE.y, top = 1.05 * self.REGION_SIZE.y)
                        ax.xaxis.set_ticks(np.arange(0,self.REGION_SIZE.x,2))
                        ax.yaxis.set_ticks(np.arange(0,self.REGION_SIZE.y,2))
                        ax.set_aspect('equal', adjustable='box')
                    elif args[0] == "Z":
                        self.curr_pos.z = float(args[1])
                        curr_command += 1
                    elif args[0] == "P":
                        curr_power = float(args[1])
                    elif args[0] == "LOC":
                        self.local_o = V2(args[1])
                    elif args[0] == "%%%":
                        new_commands_section = not new_commands_section
                        if new_commands_section:
                            reformatted_new_cmds += "LOC\t[0, 0]\n"
                        self.local_o = V2((0, 0))
                        self.curr_pos = V3(self.TR*(-1), 0)
                        curr_power = 0
                else:
                    self.reformatted_file_text += line

            print(self.reformatted_file_text.split("%%%"))
            before, middle, after = self.reformatted_file_text.split("%%%")
            self.reformatted_file_text = before + "%%%\n\n# " + datetime.now(timezone("US/Eastern")).strftime("%Y-%m-%d %H:%M:%S") + "\n" + middle + reformatted_new_cmds + after
            
            log_file.close()
            
            plt.text(-110.0, 3.0, "{} s = {} min".format(int(10*total_time)/10.0, int(100*total_time/60.0)/100.0), fontsize=12)
            plt.show()
    
        except FileNotFoundError:
            print("{}{} not found.".format(PATH_PREFIX, self.sample_name))

    def run(self, event):
        plt.close()
        self.update_sample_history()
        self.continue_to_run = True

    def cancel(self, event):
        plt.close()
        self.continue_to_run = False
            
    # returns the duration of the write
    def render_write_line(self, ax, start, end, speed, color):
        
        t = self.render_move_to_start(ax, start)
        l = mlines.Line2D([start.x, end.x], [start.y, end.y], color=color)
        ax.add_line(l)
        self.curr_pos.setXY(end)
        return t + (end - start.asV2()).magnitude / speed

    def render_move_to_start(self, ax, start):
        
        if start != self.curr_pos.asV2():       # then at least calculate the time to move to start
            if (not self.connect_keithley):          # then map move to start
                l = mlines.Line2D([self.curr_pos.x, start.x], [self.curr_pos.y, start.y], linestyle=':', color='lightgray')
                ax.add_line(l)
            return (start - self.curr_pos.asV2()).magnitude / self.default_speed
        return 0

    def update_sample_history(self):
        log_file = open(PATH_PREFIX + self.sample_name + ".txt", "w")
        log_file.write(self.reformatted_file_text)
        log_file.close()
