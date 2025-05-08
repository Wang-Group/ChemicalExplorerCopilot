from MS_hotplate import HotPlateController as Hotplate
from serial import Serial

ser_config = {
    "port": "<insert port here>",
    "baudrate": 115200,
    "timeout": 0.1
}
ser = Serial(**ser_config)
hotplate = Hotplate(ser, logger="<insert logger here>")

# Set temperature to 100 degrees
hotplate.set_temp(100)
hotplate.turn_heater_on()
# turn off heater
hotplate.turn_heater_off()
# set stirrer speed to 100 rpm
hotplate.set_rpm(100)
hotplate.turn_stir_on()
# turn off stirrer
hotplate.turn_stir_off()
