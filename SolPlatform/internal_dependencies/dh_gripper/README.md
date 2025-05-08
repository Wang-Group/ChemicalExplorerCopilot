# dh_gripper

## Description

This library is used to control the servo gripper from dh robotics.

## How This Library Works

The dh_gripper library is used to control the servo gripper from dh-robotics.
The grippers can be controlled by Modbus RTU protocol. This library is based on the serial communication.

## Installation

Use this to install the package.

```
pip install -e .
```

## Use the library

Example can be found in [`example.py`](./example.py)
The example include some functions like initialization, set the position of finger, gripper rotation, and set the force and speed of the gripper.

```python
from dh_gripper import Gripper
from serial import Serial

# Create a serial connection to the gripper
ser_config = {
    'port': '<insert port here>',
    'baudrate': 115200, 
    'timeout': 0.1}
ser = Serial(**ser_config)
gripper = Gripper(ser = ser, slave = '<insert slave>', _logger = '<insert logger>', name = '<insert Gripper model>')

# Initialize the gripper
gripper.initialization()
# Close the gripper
gripper.set_site(0)
# Open the gripper
gripper.set_site(1000)
# set the speed of the gripper
gripper.set_speed(100)
# set the force of the gripper
gripper.set_force(100)
# set the angle of the gripper
gripper.set_rotation_angle(180)
# set the rotation speed of the gripper
gripper.set_rotation_speed(100)
# set the rotation force of the gripper
gripper.set_rotation_force(100)

```

## Support

To get the manual of the hardware, go to [DH-Robotics](https://en.dh-robotics.com/) to find more informations.

## Authors

[Enyu He](409476555@qq.com), [Lin Huang](huanglin1757@stu.xmu.edu.cn) while working in [Wang Group](https://cwang.xmu.edu.cn/)

## License
