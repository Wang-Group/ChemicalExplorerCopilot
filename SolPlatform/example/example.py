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
