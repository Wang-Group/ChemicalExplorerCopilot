# leadshine_driver

## Description

This library is used to control the leadshine driver (DM2C, CL2C series) which is used to control the stepper motor.
## How This Library Works
The driver can be controlled by Modbus RTU protocol. This library is based on the serial.

## Installation

Use this to install the package.

```
pip install -e .
```
## Use the library
Example can be found in [`example.py`](./example.py)
The example include some functions like return axis to home position, move to absolute position, rotate under a selected speed.

```python
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
```
The example config file can be found in [`config.yaml`](./config.yaml)
```yaml
peak_current: 30 # unit: 0.1 A
pulse_circle: 10000
pitch_of_screws: 4
moving_param: [10, 30, 20] # [acc, dec, defualt_speed] 
datum_param: [20, 1, 500, 500, 5] # [datum_rapid_speed, datum_slow_speed, datum_acc, datum_dec, datum_mode]
ip: 
  datum_in: Pr4.04
op: 
  brk: Pr4.12
  relay: Pr4.11
```
## Support
To get the manual of the hardware, go to [Leadshine](https://www.leadshine.com/) to find more informations.
## Authors

[Lin Huang](huanglin1757@stu.xmu.edu.cn) while working in [Wang Group](https://cwang.xmu.edu.cn/)

## License