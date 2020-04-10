#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import visa
import numpy as np

"""
The keithley object that will manage the transmission of data and commands.

author: T. Max Roberts
"""

class Keithley:
    
    def __init__(self, addr = 24):
        try:
            rm = visa.ResourceManager()
            self.keith = rm.open_resource('GPIB0::%i::INSTR' %(addr))        
            self.run_start_up_commands()           
        except:
            print("Something went wrong...")
            sys.exit(0)
        
    def run_start_up_commands(self):
        for com in start_up_commands:
            self.send_command(com)
            time.sleep(.01)

    def send_command(self, command):
        response = self.keith.write(command)
        if response != '':
            return response
        else:
            return None
        
    """   all the useful commands as methods   """

    def reset(self):
        self.send_command('*RST')

    def set_output_on(self):
        self.send_command(':OUTP ON')

    def set_output_off(self):
        self.send_command(':OUTP OFF')

    def set_source_type(self, source_type):
        source_type = source_type.lower()
        if source_type == 'current' or source_type == 'curr' or source_type == 'c':
            self.send_command(':SOUR:FUNC CURRENT')
        elif source_type == 'voltage' or source_type == 'volt' or source_type == 'v':
            self.send_command(':SOUR:FUNC VOLT')
        else:
            print("Unknown source setting!")

    def set_source_voltage(self, voltage):
        if type(voltage) == int or type(voltage) == float:
            if voltage > 200:
                voltage = 200
                print("Voltage limits are  +/- 200 V")
            if voltage < -200:
                voltage = -200
                print("Voltage limits are  +/- 200 V")
            self.set_source_type('voltage')
            self.send_command(':SOUR:VOLT %s' %voltage)
        else:
            print("Bad voltage sent")

    def set_source_current(self, current):
        if type(current) == int or type(current) == float:
            if current > 1:
                current = 1
                print("Current limits are  +/- 1 A")
            if current < -1:
                current = -1
                print("Current limits are  +/- 1 A")
            self.set_source_type('current')
            self.send_command(':SOUR:CURR %s' %current)
        else:
            print("Bad current sent")

    def set_sensor_type(self, sensor_type):
        sensor_type = sensor_type.lower()
        if sensor_type == 'current' or sensor_type == 'curr' or sensor_type == 'c':
            self.send_command(':SENS:FUNC "CURR"')
            return 'current'
        elif sensor_type == 'voltage' or sensor_type == 'volt' or sensor_type == 'v':
            self.send_command(':SENS:FUNC "VOLT"')
            return 'voltage'
        else:
            print("Unknown sensor setting!")
            return None

    def set_sensor_range(self, sensor_type, sensor_range):
        sensor_type = self.set_sensor_type(sensor_type)
        print("Sensor type set to %s" %sensor_type)
        if type(sensor_range) == int or type(sensor_range) == float:
            order = int(('%.2E' %sensor_range)[5:])
            if sensor_type == 'voltage':
                self.send_command(':SENS:VOLT:RANG 10E%s' %order)
            elif sensor_type == 'current':
                self.send_command(':SENS:CURR:RANG 10E%s' %order)
            else:
                print("Shouldn't get here!")
        else:
            print("Bad range sent.")

    def set_voltage_compliance(self, limit):
        if type(limit) == int or type(limit) == float:
            coeff = float(('%.2E' %limit)[:3])
            order = int(('%.2E' %limit)[5:])
            self.send_command(':SENS:VOLT:PROT %sE%s' %(coeff, order))
        else:
            print("Bad compliance value sent.")

    def set_current_compliance(self, limit):
        if type(limit) == int or type(limit) == float:
            coeff = float(('%.2E' %limit)[:3])
            order = int(('%.2E' %limit)[5:])
            self.send_command(':SENS:CURR:PROT %sE%s' %(coeff, order))
        else:
            print("Bad compliance value sent.")

    def set_num_triggers(self, num):
        if type(num) == int:
            if num < 1:
                print("Number of triggers must be between 1-2500")
                print("Triggers set to 1")
                num = 1
            if num > 2500:
                print("Number of triggers must be between 1-2500")
                print("Triggers set to 2500")
                num = 2500
            self.send_command(':TRIG:COUN %s' %num)
        else:
            print("Bad trigger value sent.")

    def get_num_triggers(self):
        response = self.get_response(':TRIG:COUN?')
        return int(response.replace(' ', ''))

    def read(self, data_type=None):
        if data_type == None:
            self.send_command(':FORM:ELEM TIME, VOLT, CURR, RES')
        elif data_type.lower() == 'v':
            self.send_command(':FORM:ELEM TIME, VOLT')
        elif data_type.lower() == 'c':
            self.send_command(':FORM:ELEM TIME, CURR')
        elif data_type.lower() == 'r':
            self.send_command(':FORM:ELEM TIME, RES')
        else:
            self.send_command(':FORM:ELEM TIME, VOLT, CURR, RES')
        self.send_command(':OUTP ON')
        time.sleep(.25)
        self.send_command(':INIT')
        time.sleep(.25)
        # FETCH? waits for INIT to complete
        response = self.get_response(':FETCH?')
        time.sleep(.25)
        self.send_command(':OUTP OFF')
        return parse_data(response, data_type=data_type)

    """
    # delay = pulse time at each current;  rel_gap_delay = relative length of gap between pulses
    #   (e.g., 0.25 = 1/4 gap per 1 pulse => 0.2 : 0.8 = gap : pulse)
    def current_sweep(self, start, stop, step=0.02, delay=0.1, rel_gap_delay=0.25):
        
        if gap_delay == 0:
            sweep_list = range(start, stop + step, step)
        else:
            sweep_list =
        # ...
        
        trig_count = (stop-start)/step + 1
        self.send_command('*RST')                   # restore GPIB default conditions
        self.send_command(':SENS:FUNC:CONC OFF')    # turn off current configurations
        self.send_command(':SOUR:FUNC CURR')        # current source
        self.send_command(":SENS:FUNC 'VOLT'")      # monitor voltage
        self.send_command(':SENS:VOLT:PROT 7.5')    # set 7.5V voltage compliance
        self.send_command('SOUR:CURR:MODE LIST')    # list current sweep mode
        self.send_command('SOUR:LIST:CURR %s' %(sweep_list))        # list current sweep mode
        self.send_command(':TRIG:COUNT %i' %(count(sweep_list)))    # set sweep points
        self.send_command(':SOUR:DEL %f' %(adj_delay))              # set source delay
        self.send_command(':OUTP ON')               # turn on source output
        self.send_command(':READ?')                 # trigger sweep, request data
    """

    """
    def sweep(self, data_type=None, start=-10, stop=10, step=1, delay=0.1, num_sweeps=1):
        sweep_points = (stop-start)/step + 1
        num_trigs = num_sweeps*sweep_points
        if data_type == None:
            self.send_command(':FORM:ELEM TIME, VOLT, CURR, RES')
        elif data_type.lower() == 'v':
            self.send_command(':FORM:ELEM TIME, VOLT')
        elif data_type.lower() == 'c':
            self.send_command(':FORM:ELEM TIME, CURR')
        elif data_type.lower() == 'r':
            self.send_command(':FORM:ELEM TIME, RES')
        else:
            self.send_command(':FORM:ELEM TIME, VOLT, CURR, RES')
        self.send_command(':SOUR:FUNC VOLT')
        time.sleep(delay)
        self.send_command(":SENS:FUNC 'CURR:DC'")
        time.sleep(delay)
        self.send_command(':SENS:CURR:PROT 0.5')
        time.sleep(delay)
        self.send_command(':SOUR:VOLT:START %s' %start)
        time.sleep(delay)
        self.send_command(':SOUR:VOLT:STOP %s' %stop)
        time.sleep(delay)
        self.send_command(':SOUR:VOLT:STEP %s' %step)
        time.sleep(delay)
        self.send_command(':SOUR:VOLT:MODE SWE')
        time.sleep(delay)
        self.send_command(':SOUR:SWE:RANG AUTO')
        time.sleep(delay)
        self.send_command(':SOUR:SWE:SPAC LIN')
        time.sleep(delay)
        self.send_command(':SOUR:SWE:POIN %s' %sweep_points)
        time.sleep(delay)
        self.send_command(':TRIG:COUN %s' %num_trigs)
        time.sleep(delay)
        self.send_command(':SOUR:DEL 0.1')
        time.sleep(delay)
        self.send_command(':OUTP ON')
        time.sleep(delay)
        self.send_command(':INIT')
        # FETCH? waits for INIT to complete
        response = self.get_response(':FETCH?')
        time.sleep(.25)
        self.send_command(':OUTP OFF')
        return parse_data(response, data_type=data_type)
    """


"""
This function parses the data returned from the Keithley.
The data is stuctured as {Volts, Amps, Ohms, Timestamp, Status}.
This creates an array of {Time, Volts, Amps, Ohms}.
Each element is a column vector for easy plotting.
KEYWORDS:
data_type = 'v' returns only time and volts, 'c', only time and current,
'r' only time and ohms.
"""
def parse_data(data, data_type=None):
    # Clean up the strings, splits into list
    data = data.replace(' ', '').split(',')
    # Reshape in sections
    if data_type in ['v', 'c', 'r']:
        cols = 2
    else:
        cols = 4
    # NOTE If data is not returned in groups of "cols" this will drop elements!
    data = zip(*[iter(data)]*cols)
    # Use an array as they can be indexed, and for type conversion
    data = np.array(data).astype(np.float)
    if data_type == None:
        return np.array([data[:,3], data[:,0], data[:,1], data[:,2]])
    elif data_type.lower() == 'v':
        return np.array([data[:,1], data[:,0]])
    elif data_type.lower() == 'c':
        return np.array([data[:,2], data[:,0]])
    elif data_type.lower() == 'r':
        return np.array([data[:,3], data[:,0]])
    else:
        print("Bad data_type given, returning full data set")
        return np.array([data[:,3], data[:,0], data[:,1], data[:,2]])

"""  Fast Settings  """
start_up_commands = ["*RST",
                     ":SYST:TIME:RES:AUTO 1",
                     ":SYST:BEEP:STAT 0",
                     ":SOUR:FUNC CURR",
                     ":SENS:FUNC:CONC OFF",
                     ":SENS:AVER:STAT OFF",
                     ":SENS:CURR:NPLC 0.01",
                     ":SENS:VOLT:NPLC 0.01",
                     ":SENS:RES:NPLC 0.01",
                     ":SENS:FUNC 'VOLT'",
                     ":SENS:VOLT:RANG 1e1",
                     ":TRIG:DEL 0.0",
                     ":SYST:AZER:STAT OFF",
                     ":SOUR:DELAY 0.0",
                     ":DISP:ENAB OFF"]

class FakeKeithley(object):
    def __init__(self):
        for method in Keithley.__dict__:
            self.__dict__[method] = self.fake_method
    def fake_method(self, *arg, **kwarg):
        pass
