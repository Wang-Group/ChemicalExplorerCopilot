# pHTestunio

## Description

This library is used as pH meter controller.
## How This Library Works

This pH meter is consist of a pH data acquisition board which can transfer pH into the analog, and an Ardunio Uno R3 board is used to read the analog.
## Installation

Use this to install the package.
```
pip install -e .
```
Before using this, the [commandunio](https://github.com/croningp/commanduino) library should be installed first.
```
git clone https://github.com/croningp/commanduino.git
cd commanduino
python setup.py install  # May require the use of sudo
```
## Use the library
Before use the library, the ardunio program of data acquisition should be uploaded into the arduino board.  
The demo of the program can be found in [`firmware/pH_test_demo/pH_test_demo.ino`](./firmware/pH_test_demo/pH_test_demo.ino).  
```cpp
#include <CommandHandler.h>
#include <CommandManager.h>
CommandManager cmdMng;

#include <CommandAnalogRead.h>
const int pH_pin = A1;
CommandAnalogRead ar1(pH_pin);

void setup()
{
  Serial.begin(115200);

  ar1.registerToCommandManager(cmdMng, "A1");

  cmdMng.init();
}

void loop()
{
    cmdMng.update();
}
```
Example can be found in [`example.py`](./example.py)
The example include some functions like record the pH of the buffer, calibrate, read pH.

```python
from pHTestuino import pHTestMeter

meter = pHTestMeter(port="<insert port here>", logger="<insert logger here>")

# record a pH value (4.00)
meter.record_ref(4.00)
# record a pH value (7.00)
meter.record_ref(7.00)
# record a pH value (10.00)
meter.record_ref(10.00)
# calibrate the meter
meter.calibrate_meter()

# read a pH value
meter.read_pH()
```

## Support
The pH data acquisition board can be accessible in [DIY MORE](https://www.diymore.cc/products/diymore-liquid-ph-value-detection-detect-sensor-module-monitoring-control-for-arduino-m).  
To get the manual of the Arduino Uno R3 board, go to [Arduino](https://www.arduino.cc/) to find more informations.  
The control of arduino is based on the open-source [commandunio](https://github.com/croningp/commanduino) library from [Cronin Group](http://www.chem.gla.ac.uk/cronin/).

## Authors

[Lin Huang](huanglin1757@stu.xmu.edu.cn) and [Yibin Jiang](yibin_jiang@outlook.com) while working in [Wang Group](https://cwang.xmu.edu.cn/)

## License