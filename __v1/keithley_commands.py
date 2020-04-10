
import time
import keithley_init as kc

keith = kc.Keithley()

keith.set_source_current(0.6)
keith.set_voltage_compliance(10)

"""
  speed  |  amps  |  distance -> delay
   0.20     0.40
   0.19     0.40
   0.18     0.40
   0.
0.4       
0.4
0.4
0.4
0
0.42
0.42
0.42
0.42
0
...


def delay_controlled_sweep(

keith.set_output_on()
time.sleep(1)           # seconds
keith.set_output_off()

"""
