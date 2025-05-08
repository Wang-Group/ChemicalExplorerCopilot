# MS_hotplate

## Description

This library is used to control the hotplate from DLAB which is used to control the hotplate.
## How This Library Works
The hotplate can be controlled by MS protocol. This library is based on the serial.

## Installation

Use this to install the package.

```
pip install -e .
```
## Use the library
Example can be found in [`example.py`](./example.py)
The example include some functions like set temperature, set stir speed, turn on/off heater, turn on/off stirrer.

```python
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
```

## Support
To get the manual of the hardware, go to [DLAB](https://www.dlabsci.com/) to find more informations.
## Authors

[Chao Zhang](Zhangchao@henu.edu.cn), [Yibin Jiang](yibin_jiang@outlook.com) while working in [Wang Group](https://cwang.xmu.edu.cn/)

## License