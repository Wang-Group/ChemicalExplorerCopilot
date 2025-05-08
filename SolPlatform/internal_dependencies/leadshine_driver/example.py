from leadshine_driver import LeadShine_Controller
from serial import Serial
import yaml

with open(r"motion_param.yaml", "r") as f:
    motion_param = yaml.load(f)

ser_config = {
    "port": "<insert port here>",
    "baudrate": 115200,
    "timeout": 0.1
}
ser = Serial(**ser_config)
controller = LeadShine_Controller(ser, slave="<insert slave here>", motion_param=motion_param, logger="<insert logger here>")

# Move to home position
controller.datum()
# Move to position 1000
controller.absolute_move(1000,speed=100)
# jog at 100 rpm/other unit
controller.jog(100)