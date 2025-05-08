# zmotion

## Description

This library is used to control the motion control card from zmotion which is used to control the servo motor.
## How This Library Works
These motion control card can be controlled by TCP/IP protocol. This library is based on the ctype.
## Installation

Use this to install the package.

```
pip install -e .
```
## Use the library
Example can be found in [`example.py`](./example.py) 
The example include functions of motion of servo motor.

```python
import yaml
from zmotion import AxisMotion

with open('config.yaml') as f:
    config = yaml.safe_load(f)

axis = AxisMotion(motion_prm=config, logger="<insert logger here>")

# move to home position
axis.datum(axis_index="x")
# move to position 100
axis._absolute_move(axis_index="x", position=100)
# all axes move to home position
axis.datum_xyz()
# all axes move to position 100
axis._move_xyz([100, 100, 100, 100])

```

## Support
To get the manual of the hardware, go to [Zmotion](https://www.zmotionglobal.com/) to find more informations.
## Authors

[Enyu He](409476555@qq.com), [Yuanxiang Ye]() and [Lin Huang](huanglin1757@stu.xmu.edu.cn) while working in [Wang Group](https://cwang.xmu.edu.cn/)

## License