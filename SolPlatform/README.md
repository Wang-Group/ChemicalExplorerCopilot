# Solplatform

## Description

This library is used to control the hardware of the whole platform. The experiments on the platform are also recorded [here](./experiments/). 

## How This Library Works

This is a python library used to control the devices of three different workstations. Based on that, the platform can realize general methods of inorganic synthesis like add liquid, add solid, heat, adjust pH, and filtration.
Additionally, The LLMManager could perform the experiment from a json file which was exported from the nature language by the AI copilot.

## Installation

Before install the library, the control library of the devices should be installed first. Go to the individual folder, and run 
```
pip install -e .
```
1. [DH-Gripper](./internal_dependencies/dh_gripper): the package to control the grippers from DH robotics. 
2. [Dobot MG400](./internal_dependencies/dobot-mg400_arm): the pakcage to control the MG400 robotic arm from Dobot. 
3. [Bopai_controller](./internal_dependencies/GAS_controller): the packages to control the PLCs from Bopai, which can be used to control motors for the axis motion. 
4. [Leadshine_driver](./internal_dependencies/leadshine_driver): the packages to control the stepper motors from Leadshine. 
5. [DLAB_hotplate](./internal_dependencies/ms_h_hotplate): the package to control the temperature and stirring speed of the hotplate from DLAB. 
6. [pH_meter](./internal_dependencies/phtestunio): the package to read the pH using pH probe and arduino. this was be integrated with the control of syringe pumps to adjust the pH.
7. [Runze_devices](./internal_dependencies/runze_driver): the package to control the pumps and valves from Runze. 
8. [Zmotion_controller](./internal_dependencies/zmotion_controller): the package to control the PLC from Zmotion based on the .dll file. 


Note: The control of the [XPR balance](https://www.mt.com/sg/en/home/products/Laboratory_Weighing_Solutions/analytical-balances/automatic-balance.html) is via the SOAP communication from METTLER TOLEDO and should be acquired from the official website. Unfortunately, we can not share it due to legal concerns.

Then use the same command in this folder to install the solplatform package.

```
pip install -e .
```

## Use the library

Example can be found in [example/example.py](./example/example.py)
The example include some functions of PlatformManager like add solid, add liquid, transferliquid, adjust temperature, adjust pH and filtration.
Besides, the example of LLMManager is included.

```python
from solplatform import PlatformManager, LLMManager
import logging
logging.basicConfig(
    filename=f"./logs.txt",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%m-%d-%y %H:%M:%S",
)
logger = logging.getLogger()
# initialize the platform manager
platform_config_path = r"SolPlatform\solplatform\configs\platform_config.yaml"
SS_mapping_path = r"SolPlatform\solplatform\configs\solid_station_mapping.json"
LS_mapping_path = r"SolPlatform\solplatform\configs\liquid_station_mapping.json"
FS_mapping_path = r"SolPlatform\solplatform\configs\filtration_station_mapping.json"
manager = PlatformManager(
    platform_config_path,
    SS_mapping_path,
    LS_mapping_path,
    FS_mapping_path, 
    logger=logger,
    initialize_operation=True
)

# add solid to a vial
manager._add_solid(reactor="<insert reactor name>", solid="<insert solid name>", quantity="<insert quantity>", tolerance="<insert tolerance>")
# add liquid to a vial
manager._add_liquid(reactor="<insert reactor name>", solution="<insert liquid name>", volume="<insert volume>")
# transfer liquid from one vial to another
manager._transfer_liquid(reactor_0="<insert reactor name>", reactor_1="<insert reactor name>", volume="<insert volume>")
# adjust temperature for a vial/stir the vial
manager._adjust_temperature_for_vial(reactor="<insert reactor name>", temperature="<insert temperature>", stir_speed="<insert stir speed>")
# filter the mixture
manager.filtration_station.filtration(reactor="<insert reactor name>")
# adjust pH of a liquid
manager.liquid_station._adjust_pH_to(target_pH="<insert target pH>")

# initialize the LLM manager
materials_path = r".\example_materials.json"
json_path = r".\example.json"
mail_config_path, = r"SolPlatform\solplatform\configs\mail_config.yaml"
llm_manager = LLMManager(
    platform_config_path,
    SS_mapping_path,
    LS_mapping_path,
    FS_mapping_path,
    materials_path,
    json_path,
    mail_config_path,
    logger=logger,
    initialize_operation=True
)
# check all procedures
llm_manager.check_all_procedures()
# perform an experiment
llm_manager.perform_exp()
```

## Support

## Authors

[Yibin Jiang](yibin_jiang@outlook.com) and [Lin Huang](huanglin1757@stu.xmu.edu.cn) while working in [Wang Group](https://cwang.xmu.edu.cn/) in Xiamen University.

## License
