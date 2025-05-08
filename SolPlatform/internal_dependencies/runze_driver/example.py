from runze_driver import (SyringePump, SwitchValve, PeristalticPump, Injector)
from serial import Serial

ser_config = {
    'port': '<insert port here>',
    'baudrate': 9600,
    'timeout': 0.1
    }

ser = Serial(**ser_config)

sy_pmup = SyringePump(ser, 
                      slave="<slave1>", 
                      model="<insert pump model e.g. 'SY-03B'>", 
                      volume="<insert the max volume of the pump>", 
                      logger="<insert logger here>")
sw_vlv = SwitchValve(ser, slave="<slave2>", 
                     channel_num="<insert channel number>", 
                     model="<insert valve model e.g. 'SV-07'>", 
                     logger="<insert logger here>") 
pr_pump = PeristalticPump(ser, 
                          slave="<slave3>", 
                          logger="<insert logger here>")
inj = Injector(ser, slave="<slave4>", 
               model="<insert pump model e.g. 'SY-08'>", 
               max_tip_volume="<insert the max tip volume>", 
               volume="<insert the max volume of the pump>", 
               logger="<insert logger here>")

# Example of using the syringe pump

# initialize the pump
sy_pmup.forced_reset()
# switch the channel of the pump if needed
sy_pmup.valve_switch(param="<dict: valve index>", channel="<channel_key>")
# move the piston to the desired position
sy_pmup.move_to_absolute_position(absolute_volume="<desired volume>")

# Example of using the switch valve

# initialize the valve
sw_vlv.reset_to_origin()
# switch the valve to the desired channel
sw_vlv.valve_switch(param="<dict: valve index>", channel="<channel_key>")

# Example of using the peristaltic pump

# set the speed of the pump
pr_pump.set_dynamic_speed(speed="<desired speed>")
# stop the pump
pr_pump.set_dynamic_speed(speed=0)

# Example of using the injector

# initialize the injector
inj.initialization()
# absorb the liquid
inj.absorb(volume="<desired volume>")
# inject the liquid
inj.inject()
