# Dobot_Arms

## Description

This library is used to control the MG400 from Dobot.
## How This Library Works
The Dobot_Arms library is used to control the 4-Axis MG400 from dh-robotics.  
The robotic arm can be controlled by TCP/IP protocol. This library is based on the socket.

## Installation

Use this to install the package.

```
pip install -e .
```
## Use the library
Example can be found in [`example.py`](./example.py)
The example include some functions like initialization, set the speed of Arm moving, move the Arm to the target position based on Cartesian Coorinates.

```python
from Dobot_Arms import MG400

ip = "<input your arm's ip>"

my_arm = MG400(ip = ip)
# Initialize the robot
my_arm.initialize_robot()
# Set the speed of the robot
my_arm.SetSpeedL(50)
# Move the robot to the position [0, 0, 0, 0]
my_arm.MoveL([0, 0, 0, 0])
```

## Support
This library is based on a open source github library from [Dobot](https://www.dobot-robots.com/): [TCP-IP-4Axis-Python](https://github.com/Dobot-Arm/TCP-IP-4Axis-Python)
To get the manual of the hardware, go to [Dobot](https://www.dobot-robots.com/) to find more informations.

## Authors

[Lin Huang](huanglin1757@stu.xmu.edu.cn) and [Yibin Jiang](yibin_jiang@outlook.com) while working in [Wang Group](https://cwang.xmu.edu.cn/)

## License