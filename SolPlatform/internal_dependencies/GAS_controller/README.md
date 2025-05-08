# GAS_controller

## Description

This library is used to control the bopai motion control card.
## How This Library Works
The card can be controlled by AT command. This library is based on the serial.

## Installation

Use this to install the package.

```
pip install -e .
```
## Use the library
Example can be found in [`example.py`](./example.py)
The example include some functions like return axis to home position, move to absolute position, rotate under a selected speed, set analog, get analog, set output signal, get input signal.

```python
import yaml
from Gas_controller import GASAxis

with open(r'config.yaml') as f:
    config = yaml.safe_load(f)

axis = GASAxis(config, logger='<insert logger here>')

# Move the axis to home position
axis.return_home(axis_index='x')
# Move the axis to a specific position
axis.trap(axis_index='x', position=100, speed=50)
# Jog mode
axis.jog(axis_index='x', speed=300)
# set output signal
axis.output_trigger(op_index='<input the output index>', onoff=True)
# set analog output
axis.analog_trigger(dac_index='<input the dac index>', voltage="<input the voltage>")
# get analog input
axis.read_analog(adc_index='<input the adc index>')
```
The example config file can be found in [`config.yaml`](./config.yaml)
```yaml
connection_param:
  port: "COM28"
  baudrate: 115200
  parity: "N"
  timeout: 0.1
axis:
  z: 1
  spin: 2
  stir: 3
  spec_waste_pump: 4 
  stir_storage: 5
axis_list: [1, 2, 3, 4, 5]
ip: # [LimitN, LimitP]
op:
  stir: 0
  actuator: 1 
  air_gripper: 2
  magnetic: 3
dac: 
      
adc: 

motor_param: # [pulse/rev, pitch_of_screws]
  1: [6400, 1]
  2: [25600, 360]
  3: [6400, 60]
  4: [6400, 60]
  5: [6400, 60]
trap_param: # [dAcc, dDec, dSmoothTime, dVelStart]
  1: [5, 5, 0, 0]
  2: [40, 450, 0, 0]
jog_param: # [dAcc, dDec, dSmoothTime]
  1: [50, 30, 0]
  2: [50, 30, 0]
  3: [200, 300, 0]
  4: [200, 300, 0]
  5: [300, 300, 2]
home_param: # [nHomeMode, nHomeDir, lOffset, dHomeRapidVel, dHomeLocatVel, dHomeIndexVel, dHomeAcc]
  1: [1, 0, 0, 10, 1, 0, 100]
  2: [1, 0, 0, 10, 1, 0, 100]
safe_coordiniate:
  z: 0
```


## Authors

[Enyu He](409476555@qq.com), [Lin Huang](huanglin1757@stu.xmu.edu.cn) while working in [Wang Group](https://cwang.xmu.edu.cn/)

## License