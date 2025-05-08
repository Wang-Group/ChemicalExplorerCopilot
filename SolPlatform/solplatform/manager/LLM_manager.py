import json
import time
import llmlab
import numpy as np
import llmlab.operations.exp_operation.add
from logging import Logger
from copy import copy, deepcopy
from llmlab.converter.llm_link.NL_manager import NLManager
from llmlab.converter.llm_link.constants.units import UNITS
from solplatform import PlatformManager
from datetime import datetime, timedelta
from solplatform.manager.manager import DEFULT_STIR_SPEED
from solplatform.manager.utility import MailSender, check_obj_status, exp_name_from_file_path


supported_operation_types = [
    llmlab.operations.exp_operation.AddSolid,
    llmlab.operations.exp_operation.AddLiquid,
    llmlab.operations.exp_operation.TransferLiquid,

    llmlab.operations.exp_operation.AdjustTemperatureTo,
    llmlab.operations.exp_operation.AdjustTemperatureForDuration,

    llmlab.operations.exp_operation.StartStir,
    llmlab.operations.exp_operation.StopStir,
    llmlab.operations.exp_operation.StirForDuration,

    llmlab.operations.exp_operation.AdjustpH,

    llmlab.operations.exp_operation.Wait,

    llmlab.operations.exp_operation.Dry,
    llmlab.operations.exp_operation.Precipitate,
    llmlab.operations.exp_operation.WashSolid,
    llmlab.operations.exp_operation.Filter,
    llmlab.operations.exp_operation.Evaporate,
    llmlab.operations.exp_operation.Yield

]

class LLMManager(PlatformManager):
    """
    The Platform manager driven by LLMs.

    """
    def __init__(self, 
                 platform_config_path: str, 
                 ss_mapping_path: str, 
                 ls_mapping_path: str, 
                 fs_mapping_path: str, 
                 materials_path: str, 
                 task_path: str, 
                 mail_config_path: str, 
                 logger: Logger, 
                 initialize_operation: bool):
        """
        The initialization of platfrom manager.

        Args:
            platform_config_path: the config file path of the platform.
            ss_mapping_path: the mapping path of solid station
            ls_mapping_path: the mapping path of liquid station
            fs_mapping_path: the mapping path of filtration station
            materials_path: the materials path (json file)
            task_path: the task path (json file)
            mail_config_path: the mail config path
            logger: logger
            initialize_operation: the trigger whether initalize all devices and operations
        """
        super().__init__(platform_config_path, ss_mapping_path, ls_mapping_path, fs_mapping_path, logger, initialize_operation)
        self.nl_manager = NLManager(materials_path, task_path, logger)
        self.mail_sender = MailSender(mail_config_path, logger)
        self.logger = logger
        self.mix = False
        self.task_name = exp_name_from_file_path(task_path)
        
        with open(task_path, "r", encoding = "utf-8") as json_data:
            self.task = json.load(json_data)

    def check_all_procedures(self):
        """
        Check all error before the task from json is excuted.
        """
        # check all procedures are right from the user
        self.solid_prepare_procedure, self.liquid_prepare_procedure = self.nl_manager.check_all_procedures()
        self.parsed_functions = self.nl_manager.parsed_functions
        # get reactors holding the solutions, and we should be aware the vials can't be used
        self.reactor_with_sol = [liquid.device["reactor"] for liquid in self.nl_manager.storage_liquid if "reactor" in list(liquid.device.keys())]
        # prepare the reactors as normal 
        self.prepare_reactors()
        self.storage_solid = self.nl_manager.storage_solid
        self.storage_liquid = self.nl_manager.storage_liquid
        self.required_solid = self.nl_manager.required_solid
        self.required_liquid = self.nl_manager.required_liquid
        self.reactors = self.nl_manager.required_reactors
        self.supported_types = supported_operation_types
        self.funnels = {}
        self.initialize_vial_status()

    def initialize_vial_status(self):
        """
        initialize the content status of reactors
        """
        # the reactors are empty when system initialize 
        for vial_info in self.LS_current_mapping["Vials"].values():
            vial_info["content_status"] = "empty"
        # the content in reactors with reagent is liquid
        for reactor_name in self.reactor_with_sol:
            self.LS_current_mapping["Vials"][reactor_name]["content_status"] = "liquid"


    def find_an_empty_reactor_for_preparation(self):
        """
        Find an empty bottle for chosen liquid, if not yet, wash a bottle

        Returns:
            name of empty bottle
        """
        # roll out the reactors that have already been used for preparation
        used_reactors = self.nl_manager.required_reactors
        for storage_0 in self.current_mapping["Solutions"].values():
            for key_temp, value_temp in storage_0.items():
                if key_temp == "Reactor":
                    used_reactors.append(value_temp)
        # also add the vials that is used to hold the solutions as well
        for _reactor in self.reactor_with_sol:
            used_reactors.append(_reactor)
        # unique the used reactors
        used_reactors = list(np.unique(used_reactors))

        # get the reactor from the liquid station
        for reactor in self.LS_current_mapping["Vials"].keys():
            if not (reactor in used_reactors):
                return reactor
            
        raise ValueError("no empty reactor was found for now!")

    def prepare_solid(self, solid_prepare_procedure: list):
        """
        Check all solids before the experiments
        """
        if len(solid_prepare_procedure) == 0:
            return True
        assert len(solid_prepare_procedure) == len(self.required_solid)     
        # check each solid can be prepared correctly.
        for index in range(len(self.required_solid)):
            if solid_prepare_procedure[index] == False:
                raise ValueError(f"Solid {self.required_solid[index]} can not be prepared.")
        # check the device of each solid 
        for index in range(len(self.required_solid)):
            solid = self.required_solid[index]
            method = solid_prepare_procedure[index][0]
            storage_compound = solid_prepare_procedure[index][1]
            if not solid.MW:
                raise ValueError(f"The molecular weight for {solid} is missing. It is <{solid.MW}> now. Please add it in LLM side.")
            if method == "Solid":
                self.current_mapping["Solids"][id(solid)] = {"Stock": storage_compound.device}

    def prepare_liquid(self, 
                       liquid_prepare_procedure: list, 
                       select_volume: float = 12.0):
        """
        Prepare all needed liquids before experiments.
        Args:
            liquid_prepare_procedure: the procedure of liquid preparation.
            select_volume: selected volume of the bottle. Defaults to 12.0 mL.
        """
        if len(liquid_prepare_procedure) == 0:
            return True
        assert len(liquid_prepare_procedure) == len(self.required_liquid) # each required liquid should get a corresponding method to prepare it
        
        # check each liquid can be prepared correctly.
        for index in range(len(self.required_liquid)):
            if liquid_prepare_procedure[index] == False:
                raise ValueError(f"Solid {self.required_liquid[index]} can not be prepared.")
            
        # define the reactors that will be used to prepare the liquid
        empty_reactors = []
        for index in range(len(self.required_liquid)):
            liquid = self.required_liquid[index]
            method = liquid_prepare_procedure[index][0]
            storage_compound = liquid_prepare_procedure[index][1]

            if method == "Liquid":
                self.current_mapping["Solutions"][id(liquid)] = {"Stock": storage_compound.device}
            elif method == "Liquid_from_reactor":
                self.current_mapping["Solutions"][id(liquid)] = {"Reactor": storage_compound.device["reactor"]}
            else:
                # get the solvent name of the chosen liquid
                solvent_name = liquid.solvent.chemical_id + liquid.solvent.CAS_number
                for solvent in self.storage_liquid:
                    set1 = solvent.identity.chemical_id + solvent.identity.CAS_number
                    set1 = set(set1)
                    set2 = set(solvent_name)
                    if bool(set(set1) & set(set2)):
                        break
                    
                empty_reactor = self.find_an_empty_reactor_for_preparation()
                empty_reactors.append(empty_reactor)

                if method == "Dilute":
                    # calculate the dilution_factor
                    # make sure the units are consistent (after standaridzation, it must be the same)
                    assert liquid.concentration.unit == storage_compound.concentration.unit
                    dilution_factor = (liquid.concentration.quantity / storage_compound.concentration.quantity)
                    
                    # try to add a liquid to the empty reactor
                    target_plate, target_idx = self.place_bottle_for_addition(empty_reactor)

                    # first add the concentrated solution, then add solvent to dilute it
                    self._add_liquid(
                        empty_reactor, 
                        [storage_compound.device["pump"], solvent.device["pump"]], 
                        [select_volume * dilution_factor, select_volume * (1 - dilution_factor)], 
                        target_plate, 
                        target_idx
                        )
                    # record where the liquid is in
                    self.current_mapping["Solutions"][id(liquid)] = {"Reactor": empty_reactor}

                elif method == "Dilute_from_reactor":
                    # calculate the dilution_factor
                    # make sure the units are consistent (after standaridzation, it must be the same)
                    assert liquid.concentration.unit == storage_compound.concentration.unit
                    dilution_factor = (liquid.concentration.quantity / storage_compound.concentration.quantity)
                    # try to add a liquid to the empty reactor
                    target_plate, target_idx = self.place_bottle_for_addition(empty_reactor)
                    # get the name of the source reactor
                    source_reactor = storage_compound.device["reactor"]
                    vial_info_0 = self.search_reactor_location(reactor = source_reactor)
                    vial_info_1 = self.search_reactor_location(reactor = empty_reactor)
                    
                    # first add the solvent
                    self._add_liquid(
                        empty_reactor, 
                        [solvent.device["pump"]], 
                        [select_volume * (1 - dilution_factor)], 
                        target_plate, 
                        target_idx
                        )

                    # then transfer the solute to the solvent
                    self._transfer_liquid(
                        source_reactor, 
                        empty_reactor, 
                        select_volume * dilution_factor, 
                        vial_info_0["bottle_plate"], 
                        vial_info_1["bottle_plate"], 
                        vial_info_0["slot_index"], 
                        vial_info_1["slot_index"],
                    )
                    # record where the liquid is in
                    self.current_mapping["Solutions"][id(liquid)] = {"Reactor": empty_reactor}
                elif method == "Solid":
                    if liquid.concentration.unit == "g/mL":
                        solid_to_add = liquid.concentration.quantity * select_volume * 1000
                    elif liquid.concentration.unit == "mol/L":
                        solid_to_add = liquid.concentration.quantity * liquid.MW * select_volume
                    else:
                        raise ValueError("Unsupported unit for adding solid!")
                    # adjust the volume according to the weighing
                    weight_data = self._add_solid(
                        empty_reactor, 
                        [storage_compound.device["head"]],
                        [solid_to_add], 
                        [5])
                    calculated_volume = select_volume # FIXME
                    weight_data["solvent_volume"] = calculated_volume
                    with open(f".//prepare_materials_info_{empty_reactor}, {str(datetime.now().strftime('%Y-%m-%d, %I.%M.%S'))}.json", "w", encoding="utf-8") as f:
                        json.dump(weight_data, f, indent=4)
                    # we need to know the format of weighted data, and add liquid accordingly 
                    target_plate, target_idx = self.place_bottle_for_addition(empty_reactor)
                    self._add_liquid(
                        empty_reactor, 
                        [solvent.device["pump"]], 
                        [calculated_volume], 
                        target_plate, 
                        target_idx)
                    # record where the liquid is in now
                    self.current_mapping["Solutions"][id(liquid)] = {"Reactor": empty_reactor}

                if method == "Solid" or (method == "Dilute" and dilution_factor != 1) or (method == "Dilute_from_reactor" and dilution_factor != 1):
                    self._adjust_temperature_for_vial(reactor = empty_reactor, 
                                                      temperature = None, 
                                                      stir_speed = DEFULT_STIR_SPEED * 2, 
                                                      open_bottle = False)
        if empty_reactors != []:
            time.sleep(150)
            self.hotplate_op.hotplate.turn_stir_off()
            for reactor in empty_reactors:
                target_plate, target_idx = self.place_bottle_for_addition(reactor, "bottle_holders")
                self.move_vial_to_target_destination(reactor, target_plate, target_idx)
                # the content in the reactors which were used to prepare liquid is mixture 
                self.LS_current_mapping["Vials"][reactor]["content_status"] = "liquid"

    def AddSolid(self, 
                 function: llmlab.operations.exp_operation.AddSolid, 
                 next_step: llmlab.operations.exp_operation.BasicStep = None):
        """
        Add solid to a specific reactor
        Args: 
            function: the AddSolid function.
            next_step: the next function.
        """
        # get the info of the target reactor
        _reactor = function.reactor_name
        _solid = function.solid
        _mass = function.mass
        _stir = function.stir 
        _sitr_speed = function.stir_speed 
        _curent_reactor_info = copy(self.search_reactor_location(_reactor))
        
        if _curent_reactor_info["bottle_plate"] != "balance":
            self._original_location_of_vial_in_balance = _curent_reactor_info
        else:
            self._original_location_of_vial_in_balance = None 
            
        if _stir:
            self.logger.warning("stirring is not suporrted in the current platform! skipping it for now!")
        # find which storage to get this required solid
        solid_info = self.current_mapping["Solids"][id(_solid)]
        # convert the unit to mg
        if _mass.unit == "mol":
            quantity_to_add = _solid.MW * _mass.quantity * 1000
        elif _mass.unit == "g":
            quantity_to_add = 1000*_mass.quantity
        else:
            raise ValueError("Can not convert the unit successfully!")
        
        weight_data = self._add_solid(reactor = _reactor, 
                                      solid = [solid_info["Stock"]["head"]], 
                                      quantity = [quantity_to_add], 
                                      tolerance = [5])
        with open(f".//AddSolid, {str(datetime.now().strftime('%Y-%m-%d, %I.%M.%S'))}.json", "w", encoding="utf-8") as wdf:
            json.dump(weight_data, wdf, indent=4)
        # After adding solid into a reactor:
        current_vial_info = self.search_reactor_location(_reactor)
        if self.mix: 
            # if the origin content is empty or solid, change it to solid
            if (current_vial_info["content_status"] == "empty") or (current_vial_info["content_status"] == "solid"):
                current_vial_info["content_status"] = "solid"
            # if the origin content is liquid or mixture, change it to mixture  
            elif (current_vial_info["content_status"] == "liquid") or (current_vial_info["content_status"] == "mixture"):
                current_vial_info["content_status"] = "mixture"
            # if the status is not empty, solid, liquid, mixture, raise error
            else:
                raise ValueError(f"Unknown content_status is detected, its value is {current_vial_info['content_status']}")
            # if the status is mixture, stir the mixture then change the status into liquid
            if current_vial_info["content_status"] == "mixture":
                vial_on_holder = check_obj_status("vial", "uv_vis_holder", 0, self.LS_current_mapping)
                if not vial_on_holder:
                    original_pos = deepcopy(self.search_reactor_location(_reactor))
                    self.move_vial_to_target_destination(reactor = _reactor, 
                                                         target_plate = "uv_vis_holder", 
                                                         target_idx = 0)
                    self.pH_test_op._magnetic_stir(stir_time = 10 * 60, 
                                                   stir_speed = DEFULT_STIR_SPEED * 2)
                    self.move_vial_to_target_destination(reactor = _reactor, 
                                                         target_plate = original_pos["bottle_plate"], 
                                                         target_idx = original_pos["slot_index"])
                    current_vial_info["content_status"] = "liquid"
                else:
                    raise ValueError("the uv_vis_holder is full! cannot stir!")
                
        if type(next_step) == llmlab.operations.exp_operation.AddSolid and next_step.reactor_name == _reactor:
            pass
        else:
            if self._original_location_of_vial_in_balance != None:
                self.move_vial_to_target_destination(_reactor, 
                                                    self._original_location_of_vial_in_balance["bottle_plate"], 
                                                    self._original_location_of_vial_in_balance["slot_index"])
                
        return weight_data

    def AddLiquid(self, 
                  function: llmlab.operations.exp_operation.AddLiquid, 
                  next_step: llmlab.operations.exp_operation.BasicStep = None):
        """
        Add liquid to a specific reactor.

        Args: 
            function: the AddLiquid function.
            next_step: the next function.
        """
        # get the info of the target reactor
        _reactor_name = function.reactor_name
        _liquid = function.liquid 
        _liquid_temperature = function.liquid_temperature
        _volume = function.volume
        _pH = function.pH
        _dropwise = function.dropwise
        _stir = function.stir 
        _stir_speed = function.stir_speed
        
        if _liquid_temperature:
            self.logger.warning("controlling the temperature of the added liquid is not supported for now. Currently all the reagents are in room temperature.")
        if _pH:
            self.logger.warning("controlling the pH of the added liquid is not supported for now.")

        # move target reactor to the heater to stir, if not specify speed, stir speed is equal to 300 rpm
        if _stir:
            if _stir_speed == None:
                stir_speed = DEFULT_STIR_SPEED
            else:
                stir_speed = _stir_speed.quantity
            # we have to place the bottle to the heating mantle if stirring is required, with its bottle open
            self._adjust_temperature_for_vial(_reactor_name, temperature = None, stir_speed = stir_speed, open_bottle = True)
        else:
            # otherwise we can place it wherever we want 
            self.place_bottle_for_addition(_reactor_name, desired_plate = "bottle_holders")
        
        # get the location of the reactor where liquid should be added
        vial_info_1 = self.search_reactor_location(reactor = _reactor_name)
        
        # judge whether the liquid is storaged in reactor or liquid channel.
        liquid_info = self.current_mapping["Solutions"][id(_liquid)]
        type = list(liquid_info.keys())[0]
        # if the reactor use pipette to transfer liquid
        if type == "Reactor":
            reactor_0 = liquid_info["Reactor"]
            vial_info_0 = self.search_reactor_location(reactor = reactor_0)
            if vial_info_0["bottle_plate"] != "storage_holders":
                self.place_bottle_for_addition(reactor = reactor_0, desired_plate = "bottle_holders")
            vial_info_0 = self.search_reactor_location(reactor = reactor_0)
            if _dropwise:
                self._transfer_liquid(
                    reactor_0, 
                    _reactor_name, 
                    _volume.quantity, 
                    vial_info_0["bottle_plate"], 
                    vial_info_1["bottle_plate"], 
                    vial_info_0["slot_index"], 
                    vial_info_1["slot_index"],
                    transfer_speed = 0.1, # put a dropwise speed for the transfer 
                )
            else:
                self._transfer_liquid(
                    reactor_0, 
                    _reactor_name, 
                    _volume.quantity, 
                    vial_info_0["bottle_plate"], 
                    vial_info_1["bottle_plate"], 
                    vial_info_0["slot_index"], 
                    vial_info_1["slot_index"],
                )
                
        # if it is connected by the pump, add liquid directly 
        elif type == "Stock":
            if _dropwise:
                self._add_liquid(_reactor_name, 
                                [liquid_info["Stock"]["pump"]], 
                                [_volume.quantity],
                                vial_info_1["bottle_plate"],
                                vial_info_1["slot_index"],
                                add_speed = 0.1
                                )
            else:
                self._add_liquid(_reactor_name, 
                                [liquid_info["Stock"]["pump"]], 
                                [_volume.quantity],
                                vial_info_1["bottle_plate"],
                                vial_info_1["slot_index"]
                                )
        else:
            raise ValueError("Unsupported places to intake the original solution.")
        current_vial_info = self.search_reactor_location(_reactor_name)     
        # close the cap if the temperature of the heater is higher than 30 degrees
        if "temperature" in list(current_vial_info.keys()):
            if (current_vial_info["bottle_plate"] == "heat_bottle_holders") and (current_vial_info["temperature"] != None) and (current_vial_info["temperature"]>30):
                query_status = self.hotplate_op.hotplate.quary_info("heat_status")
                if query_status == 0:
                    self.close_bottle(reactor = _reactor_name, to_original_location = True)
        # After adding liquid into a reactor:
        if self.mix: 
            # if the origin content is empty or liquid, change it to liquid
            if (current_vial_info["content_status"] == "empty") or (current_vial_info["content_status"] == "liquid"):
                current_vial_info["content_status"] = "liquid"
            # if the origin content is solid or mixture, stir, change it to mixture 
            elif (current_vial_info["content_status"] == "solid") or (current_vial_info["content_status"] == "mixture"):
                current_vial_info["content_status"] = "mixture"
            # if the status is not empty, solid, liquid, mixture, raise error
            else:
                raise ValueError(f"Unknown content_status is detected, its value is {current_vial_info['content_status']}")
            # if the status is mixture, stir the mixture then change the status into liquid
            if current_vial_info["content_status"] == "mixture":
                vial_on_holder = check_obj_status("vial", "uv_vis_holder", 0, self.LS_current_mapping)
                if not vial_on_holder:
                    original_pos = deepcopy(self.search_reactor_location(_reactor_name))
                    self.move_vial_to_target_destination(reactor = _reactor_name, 
                                                         target_plate = "uv_vis_holder", 
                                                         target_idx = 0)
                    self.pH_test_op._magnetic_stir(stir_time = 10 * 60, 
                                                   stir_speed = DEFULT_STIR_SPEED * 2)
                    self.move_vial_to_target_destination(reactor = _reactor_name, 
                                                         target_plate = original_pos["bottle_plate"], 
                                                         target_idx = original_pos["slot_index"])
                    current_vial_info["content_status"] = "liquid"
                else:
                    raise ValueError("the uv_vis_holder is full! cannot stir!")
                
    def TrasnferLiquid(self, 
                       function: llmlab.operations.exp_operation.TransferLiquid, 
                       next_step: llmlab.operations.exp_operation.BasicStep = None):
        """
        Transfer liquid from one reactor to another reactor.
        Args: 
            function: the Transferliquid function.
            next_step: the next function.
        """
        # get the information for the target function
        _from_reactor = function.from_reactor
        _to_reactor = function.to_reactor
        _volume = function.volume 
        _stir = function.stir 
        _stir_speed = function.stir_speed
        _dropwise = function.dropwise
                
        # move target reactor to the heater to stir, if not specify speed, stir speed is equal to 300 rpm
        if _stir:
            if _stir_speed == None:
                stir_speed = DEFULT_STIR_SPEED
            else:
                stir_speed = _stir_speed.quantity
            # we have to place the bottle to the heating mantle if stirring is required
            self._adjust_temperature_for_vial(_to_reactor, temperature = None, stir_speed = stir_speed, open_bottle = True)
        else:
            # otherwise we can place it wherever we want 
            self.place_bottle_for_addition(_to_reactor, desired_plate = "bottle_holders")
            
        # find their locations
        vial_info_0 = self.search_reactor_location(_from_reactor)
        vial_info_1 = self.search_reactor_location(_to_reactor)

        # we have to run the simulations to get the right function.volume_quantity
        # check the volume to transfer
        if _volume == "all":
            volume_to_transfer = function.volume_quantity[0]*1.5 # add 50% more liquid comparing to the existing ones in the bottle
        else:
            volume_to_transfer = _volume.quantity
        
        # check if the transfer is dropwise or not 
        if _dropwise:
            # transfer the liquid
            self._transfer_liquid(
                _from_reactor, 
                _to_reactor, 
                volume_to_transfer, 
                vial_info_0["bottle_plate"], 
                vial_info_1["bottle_plate"], 
                vial_info_0["slot_index"], 
                vial_info_1["slot_index"],
                transfer_speed = 0.1
            )
        else:
            # transfer the liquid
            self._transfer_liquid(
                _from_reactor, 
                _to_reactor, 
                volume_to_transfer, 
                vial_info_0["bottle_plate"], 
                vial_info_1["bottle_plate"], 
                vial_info_0["slot_index"], 
                vial_info_1["slot_index"]
            )
        
        # close the cap if the temperature of the heater is higher than 30 degrees
        current_vial_info = self.search_reactor_location(_to_reactor)
        if "temperature" in list(current_vial_info.keys()):
            if (current_vial_info["bottle_plate"] == "heat_bottle_holders") and (current_vial_info["temperature"]!=None) and(current_vial_info["temperature"] > 30):
                query_status = self.hotplate_op.hotplate.quary_info("heat_status")
                if query_status == 0:
                    self.close_bottle(reactor = _to_reactor, to_original_location = True)
        if self.mix: 
            # if the origin content is empty or liquid, change it to liquid
            if (current_vial_info["content_status"] == "empty") or (current_vial_info["content_status"] == "liquid"):
                current_vial_info["content_status"] = "liquid"
            # if the origin content is solid or mixture, stir, change it to mixture 
            elif (current_vial_info["content_status"] == "solid") or (current_vial_info["content_status"] == "mixture"):
                current_vial_info["content_status"] = "mixture"
            # if the status is not empty, solid, liquid, mixture, raise error
            else:
                raise ValueError(f"Unknown content_status is detected, its value is {current_vial_info['content_status']}")
            # if the status is mixture, stir the mixture then change the status into liquid
            if current_vial_info["content_status"] == "mixture":
                vial_on_holder = check_obj_status("vial", "uv_vis_holder", 0, self.LS_current_mapping)
                if not vial_on_holder:
                    original_pos = deepcopy(self.search_reactor_location(_to_reactor))
                    self.move_vial_to_target_destination(reactor = _to_reactor, 
                                                         target_plate = "uv_vis_holder", 
                                                         target_idx = 0)
                    self.pH_test_op._magnetic_stir(stir_time = 10 * 60, 
                                                   stir_speed = DEFULT_STIR_SPEED * 2)
                    self.move_vial_to_target_destination(reactor = _to_reactor, 
                                                         target_plate = original_pos["bottle_plate"], 
                                                         target_idx = original_pos["slot_index"])
                    current_vial_info["content_status"] = "liquid"
                else:
                    raise ValueError("the uv_vis_holder is full! cannot stir!")
            
    def AdjustTemperatureTo(self, 
                            function: llmlab.operations.exp_operation.AdjustTemperatureTo, 
                            next_step: llmlab.operations.exp_operation.BasicStep = None, 
                            waiting_time: float = 60*10):
        """
        Adjust the temperature of specific reactor, stir when needed.
        Args: 
            function: the AdjustTemperatureTo function.
            next_step: the next function.
            waiting_time: the time of heat when cool down or up.
        """
        # get the target information 
        _reactor_name = function.reactor_name
        _temperature = function.temperature
        _adjust_method = function.adjust_method
        _stir = function.stir
        _stir_speed = function.stir_speed
        _ramp_rate = function.ramp_rate 
        
        # check if stirring is needed
        if _stir:
            if _stir_speed == None:
                stir_speed = DEFULT_STIR_SPEED
            else:
                stir_speed = _stir_speed.quantity
        else:
            stir_speed = False
        
        # if adjust temperature is just to place it at room temperature, place it randomly
        if stir_speed == False and _temperature.quantity < 25:
            self.place_bottle_for_addition(reactor = _reactor_name, desired_plate = "bottle_holders")
            if _temperature.quantity < 15:
                self.logger.warning("the tempearture is lower than 15 and can not be reached on the platform. the user should place it somewhere else.")
        # else place the bottle to the heating mantle
        else:
            # get the info of the target reactor and close the bottle
            self._adjust_temperature_for_vial(reactor = _reactor_name, 
                                              temperature = _temperature.quantity, 
                                              stir_speed = stir_speed, 
                                              open_bottle = False)
        # wait for 10 minutes to reach the temperature, and we will keep it there
        time.sleep(waiting_time)
            
    def AdjustTemperatureForDuration(self, 
                                     function: llmlab.operations.exp_operation.AdjustTemperatureForDuration, 
                                     next_step: llmlab.operations.exp_operation.BasicStep, 
                                     waiting_time: float = 10 * 60):
        """
        Adjust the temperature for a vial for sometime
        Args: 
            function: the AdjustTemperatureForDuration function.
            next_step: the next function.
            waiting_time: the time of heat when cool down or up.
        """
        # get all the target information 
        _reactor_name = function.reactor_name
        _temperature = function.temperature
        _duration = function.duration
        _adjust_method = function.adjust_method
        _stir = function.stir 
        _stir_speed = function.stir_speed
        _ramp_rate = function.ramp_rate
        _reflux = function.reflux
        
        if _adjust_method:
            self.logger.warning(f"{_adjust_method} is not supported on the platform as an adjustment method.")
        if _ramp_rate:
            self.logger.warning(f"{_ramp_rate} is not supported on the platform as a valid _ramp_rate.")
        if _reflux:
            self.logger.warning(f"Reflux is not supported on the platform.")
            
        # check if stirring is needed
        if _stir:
            if _stir_speed == None:
                stir_speed = DEFULT_STIR_SPEED
            else:
                stir_speed = _stir_speed.quantity
        else: 
            stir_speed = False
            
        # if adjust temperature is just to place it at room temperature without stirring, place it randomly
        if stir_speed == False and _temperature.quantity < 25:
            self.place_bottle_for_addition(reactor = _reactor_name, desired_plate = "bottle_holders")
            if _temperature.quantity < 15:
                self.logger.warning("the tempearture is lower than 15 and can not be reached on the platform. the user should place it somewhere else.")

            if (next_step == None) and (_duration != None) and (_duration.quantity >= 12*3600):
                end_time = str(datetime.now() + timedelta(seconds = _duration.quantity))
                content = f"send the email to the user and ask to collect sample at {end_time}"
                self.mail_sender.send_message(self.task_name, content)
                self.logger.warning(content)
                return 
            
            else:
                time.sleep(_duration.quantity)
        # else place the bottle to the heating mantle
        else:
            self._adjust_temperature_for_vial(reactor = _reactor_name, 
                                              temperature = _temperature.quantity, 
                                              stir_speed = stir_speed, 
                                              open_bottle = False) # close the bottle
            
            time.sleep(waiting_time) # wait for 10 minutes to reach the temperature
            time.sleep(_duration.quantity) # wait for the time to actually heat the vial
            # after turning the temperature for a while, place it to a room temperature place 
            self.place_bottle_for_addition(reactor = _reactor_name, desired_plate = "bottle_holders")
    
    def StartStir(self, 
                  function: llmlab.operations.exp_operation.StartStir, 
                  next_step: llmlab.operations.exp_operation.BasicStep):
        """
        Stir the vial without any additional operations.
        Args: 
            function: the StartStir function.
            next_step: the next function.
        """
        # get target function information 
        _reactor_name = function.reactor_name
        _stir_speed = function.stir_speed
        
        # stir the vial without changing the capping status
        self._adjust_temperature_for_vial(
            reactor = _reactor_name, 
            temperature = None,
            stir_speed = _stir_speed.quantity, 
            open_bottle = False)

    def StopStir(self, 
                 function: llmlab.operations.exp_operation.StopStir, 
                 next_step: llmlab.operations.exp_operation.BasicStep):
        """
        Stop the stirring of the vial
        Args: 
            function: the StopStir function.
            next_step: the next function.
        """
        # get target function information 
        _reactor_name = function.reactor_name
        # stop stirring
        self._adjust_temperature_for_vial(
            reactor = _reactor_name, 
            temperature = None,
            stir_speed = False, 
            open_bottle = False)
        
    def StirForDuration(self, 
                        function: llmlab.operations.exp_operation.StirForDuration, 
                        next_step: llmlab.operations.exp_operation.BasicStep, 
                        waiting_time: float = 60*5):
        """
        Stir the vial without any additional operations for sometime
        Args: 
            function: the StirForDuration function.
            next_step: the next function.
        """
        # get target function information
        _reactor_name = function.reactor_name
        _duration = function.duration
        _temperature = function.temperature
        _stir_speed = function.stir_speed
        
        # check if stirring is needed
        if _stir_speed == None:
            stir_speed = DEFULT_STIR_SPEED
        else:
            stir_speed = _stir_speed.quantity

        # check if tuning temperature is needed
        if _temperature == None:
            temperature = None
        else:
            temperature = _temperature.quantity

        if (temperature != None) and (temperature < 25):
            vial_on_holder = check_obj_status("vial", "uv_vis_holder", 0, self.LS_current_mapping)
            if not vial_on_holder:
                original_pos = deepcopy(self.search_reactor_location(_reactor_name))
                self.move_vial_to_target_destination(reactor = _reactor_name, 
                                                     target_plate = "uv_vis_holder", 
                                                     target_idx = 0)
                self.pH_test_op._magnetic_stir(stir_time = _duration.quantity, 
                                               stir_speed = stir_speed)
                self.move_vial_to_target_destination(reactor = _reactor_name, 
                                                     target_plate = original_pos["bottle_plate"], 
                                                     target_idx = original_pos["slot_index"])
            else:
                actual_temp = self.hotplate_op.hotplate.quary_status("actual_temp")
                if actual_temp <= 26: 
                    self._adjust_temperature_for_vial(reactor = _reactor_name, 
                                                      temperature = temperature, 
                                                      stir_speed = stir_speed, 
                                                      open_bottle = False)
                    # stir for duration
                    time.sleep(_duration.quantity)
                    # stop the stirring
                    self._adjust_temperature_for_vial(reactor = _reactor_name, 
                                                    temperature = temperature, 
                                                    stir_speed = False, 
                                                    open_bottle = False)
                else:
                    raise ValueError(f"the temperature of hotplate is too high, current temp is {actual_temp}.")

        # tune the temperature for stirring 
        else:
            self._adjust_temperature_for_vial(reactor = _reactor_name, 
                                              temperature = temperature, 
                                              stir_speed = stir_speed, 
                                              open_bottle = False)
            time.sleep(waiting_time) # wait for 5 minutes to reach the temperature
            time.sleep(_duration.quantity) # wait for the time to actually heat the vial

            # stop the stirring
            self._adjust_temperature_for_vial(reactor = _reactor_name, 
                                              temperature = temperature, 
                                              stir_speed = False, 
                                              open_bottle = False)

        # check if temperature control is required.
        # If temperature < 25, place it at UV-Vis and stir.
        # if the temperature is larger than 25, place it to heating mantle, control tempeature and stir.
        # if no temperature is required, check the location of the vial. If it is already in a platform with stirring, just do stirring. 
        # if it is not in a platform with stirring, move to UV and stir. 

    def AdjustpH(self, 
                 function: llmlab.operations.exp_operation.AdjustpH, 
                 next_step: llmlab.operations.exp_operation.BasicStep):
        """
        Adjust the pH for a specific vial
        Args: 
            function: the AdjustpH function.
            next_step: the next function.
        """
        _reactor_name = function.reactor_name
        _pH = function.pH 
        _stir = function.stir
        _stir_speed = function.stir_speed
        # get the name of the reagent
        _acid_reagent = function.acid_reagent
        _base_reagent = function.base_reagent 

        allowed_pumps = []
        if _acid_reagent.identity.chemical_id != []:
            liquid_info = self.current_mapping["Solutions"][id(_acid_reagent)]
            if "Stock" not in list(liquid_info.keys()):
                raise ValueError("Make sure pump_pH_acid are in stock. It should not be prepared from dilution.")
            else:
                possible_pumps = list(liquid_info["Stock"].keys())
                if "pump_pH_acid" in possible_pumps:
                    allowed_pumps.append("pump_pH_acid")
                else:
                    raise ValueError("pump_pH_acid is not connected to the acid for adjusting pH.")
                
        if _base_reagent.identity.chemical_id != []:
            liquid_info = self.current_mapping["Solutions"][id(_base_reagent)]
            if "Stock" not in list(liquid_info.keys()):
                raise ValueError("Make sure pump_pH_base are in stock. It should not be prepared from dilution.")
            else:
                possible_pumps = list(liquid_info["Stock"].keys())
                if "pump_pH_base" in possible_pumps:
                    allowed_pumps.append("pump_pH_base")
                else:
                    raise ValueError("pump_pH_base is not connected to the base for adjusting pH.")


        # place a warning to adjust the pH of the reactor using the platform specified acid/base
        
        # check if stirring is needed
        if _stir:
            if _stir_speed == None:
                stir_speed = DEFULT_STIR_SPEED
            else:
                stir_speed = _stir_speed.quantity
        else: 
            stir_speed = False 
        # if no stirring was applied, we will apply it anyway in the platform to adjust the pH
        if not stir_speed:
            self.logger.warning("forcing stirring during the adjustment of pH now.")
        origin_info = copy(self.search_reactor_location(_reactor_name))
        # move the reactor to the uv-vis setup
        self.move_vial_to_target_destination(_reactor_name, target_plate = "uv_vis_holder", target_idx = 0)
        # adjust the pH of the reactor
        pH_data = self.liquid_station._adjust_pH_to(target_pH = _pH, 
                                                    tolerance = 0.2,
                                                    if_calibrate = False, 
                                                    try_max = 40, 
                                                    stir_speed = stir_speed,
                                                    allowed_pumps = allowed_pumps)
        self.move_vial_to_target_destination(_reactor_name, 
                                             target_plate = origin_info["bottle_plate"], 
                                             target_idx = origin_info["slot_index"])

        with open(f".//AdjustpH, {str(datetime.now().strftime('%Y-%m-%d, %I.%M.%S'))}.json", "w", encoding="utf-8") as pHd:
            json.dump(pH_data, pHd, indent=4)
        return pH_data

    def Wait(self, 
             function: llmlab.operations.exp_operation.Wait, 
             next_step: llmlab.operations.exp_operation.BasicStep):
        """
        Wait for certain amount of time.
        Args: 
            function: the Wait function.
            next_step: the next function.
        """
        _time = function.time
        if _time.quantity == None:
            raise ValueError("Nothing to wait for.")
        else:
            if (next_step == None) and (_time != None) and (_time.quantity >= 12*3600):
                end_time = str(datetime.now() + timedelta(seconds = _time.quantity))
                content = f"send the email to the user and ask to collect sample at {end_time}"
                self.mail_sender.send_message(self.task_name, content)
                self.logger.warning(content)
                return 
            else:
                time.sleep(_time.quantity)
                return 
            
    def Dry(self, 
            function: llmlab.operations.exp_operation.Dry, 
            next_step: llmlab.operations.exp_operation.BasicStep):
        """
        Dry the compound in an atmosphere with temperature control. 
        Args: 
            function: the Dry function.
            next_step: the next function.
        """
        
        # get the target function for the information 
        _reactor_name = function.reactor_name
        _time = function.time
        _temperature = function.temperature 
        _atmosphere = function.atmosphere 
        
        # check if tuning temperature is needed
        if _temperature == None:
            temperature = None
        else:
            temperature = _temperature.quantity

        # check if the drying atmosphere is air or not. 
        if _atmosphere != "air":
            self.logger.warning(f"only air-drying is allowed for now! changing the atmosphere from {_atmosphere} to air.")

        # If the compound has been in the funnel, just dry the funnel.
        if _reactor_name in list(self.funnels.keys()):
            self.logger.warning("Drying the compound in the funnel at room temperature for some time.")
        # Add a if statement to check if the reactor now is actually a funnel or not.
        # the solid is not at the funnel and we should dry it normally 
        else:
            # if the temperature is just to place it at room temperature, place it randomly on bottle holders. 
            if (temperature != None) and (temperature < 25):
                self.place_bottle_for_addition(reactor = _reactor_name, desired_plate = "bottle_holders")
                if temperature < 15:
                    self.logger.warning("the tempearture is lower than 15 and can not be reached on the platform. the user should place it somewhere else.")

                if (next_step == None) and (_time != None) and (_time.quantity >= 12*3600):
                    end_time = str(datetime.now() + timedelta(seconds = _time.quantity))
                    content = f"send the email to the user and ask to collect sample at {end_time}"
                    self.mail_sender.send_message(self.task_name, content)
                    self.logger.warning(content)
                    return 
            
            # else place the bottle to the heating mantle
            else:
                # get the info of the target reactor and open the bottle for drying
                self._adjust_temperature_for_vial(reactor = _reactor_name, 
                                                  temperature = temperature, 
                                                  stir_speed = False, 
                                                  open_bottle = True) 
                
        if _time != None:
            if _time.quantity >= 12*3600: 
                end_time = str(datetime.now() + timedelta(seconds = _time.quantity))
                content = f"send the email to the user and ask to collect sample at {end_time}"
                self.mail_sender.send_message(self.task_name, content)
                self.logger.warning(content)
                return 
            else:
                time.sleep(_time.quantity)
            
    def Precipitate(self, 
                    function: llmlab.operations.exp_operation.Precipitate, 
                    next_step: llmlab.operations.exp_operation.BasicStep, 
                    waiting_time = 10*60):
        """
        Add compounds to precipitate the compounds
        Args: 
            function: the Precipitate function.
            next_step: the next function.
        """
        # get the information from the target function 
        _reactor_name = function.reactor_name
        _temperature = function.temperature
        _stirring_time = function.stirring_time
        _stir_speed = function.stir_speed
        _reagent = function.reagent
        _reagent_quantity = function.reagent_quantity
        _repeat = function.repeat
        
        # only support the precipitation of adding liquid for now
        if _reagent != None:
            if not isinstance(_reagent, llmlab.operations.exp_operation.Liquid):
                raise ValueError("Only adding liquid to precipitate is allowed!")
        
        for i in range(_repeat):
            # check if stirring is needed
            if _stir_speed == None:
                stir_speed = DEFULT_STIR_SPEED
            else:
                stir_speed = _stir_speed.quantity
            if stir_speed == 0:
                stir_speed = False
                
            # check if stirring is needed
            if _temperature == None:
                temperature = None
            else:
                temperature = _temperature.quantity
                
            # if adjust temperature is just to place it at room temperature, place it randomly
            if (stir_speed == False) and (temperature != None) and (temperature < 25):
                self.place_bottle_for_addition(reactor = _reactor_name, desired_plate = "bottle_holders")
                if _temperature.quantity < 15:
                    self.logger.warning("the tempearture is lower than 15 and can not be reached on the platform. the user should place it somewhere else.")
            # else place the bottle to the heating mantle
            else:                
                # get the info of the target reactor and close the bottle
                if temperature < 25:
                    temperature = 25.0
                    self.logger.warning("the temperature is smaller than 25. for the usage of stirring in heating mantle, we changed it to 25.")

                self._adjust_temperature_for_vial(
                    reactor = _reactor_name, 
                    temperature = temperature, 
                    stir_speed = stir_speed, 
                    open_bottle = False)
                # wait for 10 minutes to reach the temperature, and we will keep it there
                if temperature is not None:
                    time.sleep(waiting_time)
            
            # get the location of the reactor where liquid should be added
            vial_info_1 = self.search_reactor_location(reactor = _reactor_name)

            if _reagent is not None:
                # select a liquid to add to the vial 
                # judge whether the liquid is storaged in reactor or liquid channel.
                liquid_info = self.current_mapping["Solutions"][id(_reagent)]
                type = list(liquid_info.keys())[0]
                # if the reactor use pipette to transfer liquid
                if type == "Reactor":
                    reactor_0 = liquid_info["Reactor"]
                    self.place_bottle_for_addition(reactor = reactor_0, desired_plate = "bottle_holders")
                    vial_info_0 = self.search_reactor_location(reactor = reactor_0)
                    self._transfer_liquid(
                        reactor_0, 
                        _reactor_name, 
                        _reagent_quantity.quantity, 
                        vial_info_0["bottle_plate"], 
                        vial_info_1["bottle_plate"], 
                        vial_info_0["slot_index"], 
                        vial_info_1["slot_index"],
                    )
                        
                # if it is connected by the pump, add liquid directly 
                elif type == "Stock":
                    self._add_liquid(_reactor_name, 
                                    [liquid_info["Stock"]["pump"]], 
                                    [_reagent_quantity.quantity],
                                    vial_info_1["bottle_plate"],
                                    vial_info_1["slot_index"]
                                    )
                else:
                    raise ValueError("Unsupported places to intake the original solution.")

            # close the cap if the temperature of the heater is higher than 30 degrees
            current_vial_info = self.search_reactor_location(_reactor_name)
            if "temperature" in list(current_vial_info.keys()):
                if (current_vial_info["bottle_plate"] == "heat_bottle_holders") and (current_vial_info["temperature"] != None) and (current_vial_info["temperature"]>30):
                    query_status = self.hotplate_op.hotplate.quary_info("heat_status")
                    if query_status == 0:
                        self.close_bottle(reactor = _reactor_name, to_original_location = True)
            time.sleep(_stirring_time.quantity)
        
    
    def WashSolid(self, 
                  function: llmlab.operations.exp_operation.WashSolid, 
                  next_step: llmlab.operations.exp_operation.BasicStep):
        """
        Add compounds to wash a solid compound
        Args: 
            function: the WashSolid function.
            next_step: the next function.
        """
        
        # get all the target function information
        _reactor_name = function.reactor_name
        _solvent = function.solvent
        _volume = function.volume
        _waste_vessel = function.waste_vessel
        _stir = function.stir
        _stir_speed = function.stir_speed
        _atmosphere = function.atmosphere
        _repeat = function.repeat

        # get the current location of the solid. It should be on a funnel if wash solid is used. 
        if _reactor_name not in list(self.funnels.keys()):
            raise ValueError("Wash solid only supports washing solid on the funnels now.")
        # check that all the parameters make sense
        if _stir:
            self.logger.warning("Filtration with stirring is not supported except the mixture will be stirred before filtration.")
        if _atmosphere != "air":
            self.logger.warning("Filtration at air is supported. Changing the atmosphere to air.")

        # wash the solid with the specific solvent
        liquid_info = self.current_mapping["Solutions"][id(_solvent)]
        type = list(liquid_info.keys())[0]

        # if it is connected by the pump, add liquid directly 
        if type == "Stock":
            self.fs_axis_gripper_op.prepare_funnel(self.funnels[_reactor_name])
            self.fs_axis_gripper_op.wash_mixture(
                target_idx = self.funnels[_reactor_name], 
                solvent = liquid_info["Stock"]["pump_filtration"], 
                wash_repeat = _repeat,
                wash_time = _volume.quantity / self.fs_axis_gripper_op.solvent_factors[liquid_info["Stock"]["pump_filtration"]]) # FIXME change the wash time according to the volume to be added
            
        else:
            find_wash_port = False
            try:
                for liquid_temp in self.nl_manager.materials["Liquid"]:
                    if find_wash_port == True: 
                        break
                    else:
                        for key_temp, value_temp in liquid_temp.items():
                            if "pump_filtration" in value_temp["connection"]:
                                if key_temp == _solvent.identity.chemical_id[0]:
                                    liquid_name = (value_temp["connection"]["pump_filtration"])
                                    find_wash_port = True

                self.fs_axis_gripper_op.prepare_funnel(self.funnels[_reactor_name])
                self.fs_axis_gripper_op.wash_mixture(
                    target_idx = self.funnels[_reactor_name], 
                    solvent = liquid_name, 
                    wash_repeat = _repeat,
                    wash_time = _volume.quantity / self.fs_axis_gripper_op.solvent_factors[liquid_name]) # FIXME change the wash time according to the volume to be added 
                

            except:
                raise ValueError("Unsupported places to intake the original solution.")
    
    def Filter(self, 
               function: llmlab.operations.exp_operation.Filter, 
               next_step: llmlab.operations.exp_operation.BasicStep):
        """
        Filter a mixture of solid and liquid
        Args: 
            function: the Filter function.
            next_step: the next function.
        """
        # get all the target function information
        _reactor_name = function.reactor_name
        _target_form = function.target_form
        _filtrate_vessel = function.filtrate_vessel
        _stir = function.stir
        _stir_speed = function.stir_speed
        _temperature = function.temperature
        _atmosphere = function.atmosphere

        # check all the parameters are supported on the platform. if not, record the changes.
        if _atmosphere != "air":
            self.logger.warning("Filtration at air is supported. Changing the atmosphere to air.")
        if (_temperature != None) and (_temperature.quantity!= None) and (_temperature.quantity>=25): 
            self.logger.warning("Fitration at room temperature is supported. Changing temperature to room temperature.")
        if _stir:
            self.logger.warning("Filtration with stirring is not supported except the mixture will be stirred before filtration.")
        if _target_form == "liquid" and _filtrate_vessel =="waste":
            raise ValueError("pumping the products to waste is not correct. check the procedures again!")
        # move the reactor to the filtration stage
        self.open_bottle(_reactor_name)
        self.move_vial_to_target_destination(_reactor_name, target_plate = "motor_1_ls", target_idx = 0)
        # if target_form is liquid, we will collect the liquid in an empty vial. 
        collect = False
        if _filtrate_vessel != "waste":
            self.open_bottle(_filtrate_vessel)
            self.move_vial_to_target_destination(_filtrate_vessel, target_plate = "motor_1_ls", target_idx = 1)
            collect = True
        self.move_vial_to_target_destination(_reactor_name, target_plate = "motor_1_fs", target_idx = 0)
        # perform the filtration process and record the location of the solid
        if _target_form == "solid" or _target_form == "liquid":
            raw_funnel_idx = self.filtration_station.filtration(_reactor_name, _return = True, collect = collect, solvent = None)
        else:
            raise ValueError(f"target form can be either solid or liquid. Current form is {_target_form}.")
        # record this funnel was used in this reactor, any future operation for this reactor will be redirected to this funnel
        self.funnels[_reactor_name] = raw_funnel_idx
        # move vial to the empty position on the bottle_holders
        for reactor in [_reactor_name, _filtrate_vessel]:
            for idx in range(self.bottle_holder_capacity):
                if not check_obj_status('vial', "bottle_holders", idx, self.LS_current_mapping):
                    break
            if reactor != "waste":
                self.move_vial_to_target_destination(reactor, "bottle_holders", idx)
    
    def Evaporate(self,
                  function: llmlab.operations.exp_operation.Evaporate, 
                  next_step: llmlab.operations.exp_operation.BasicStep):
        """
        Evaporate the reactor
        Args: 
            function: the Evaporate function.
            next_step: the next function.
        """
        _reactor_name = function.reactor_name
        _pressure = function.pressure
        _stir = function.stir
        _stir_speed = function.stir_speed
        _temperature = function.temperature
        _duration = function.duration

        if _pressure:
            self.logger.warning(f"controlling pressure is not supported in the evaporation process of this platform")

        # check if stirring is needed
        if _stir:
            if _stir_speed == None:
                stir_speed = DEFULT_STIR_SPEED
            else:
                stir_speed = _stir_speed.quantity
        else: 
            stir_speed = False

        # check if tuning temperature is needed
        if _temperature == None:
            temperature = None
        else:
            temperature = _temperature.quantity

        # check if tuning temperature is needed
        if _duration == None:
            duration = 0
        else:
            duration = _duration.quantity

        # open the bottle 
        self.open_bottle(_reactor_name)

        # if adjust temperature is just to place it at room temperature, place it randomly
        if (stir_speed == False) and (temperature != None) and (temperature < 25):
            self.place_bottle_for_addition(reactor = _reactor_name, desired_plate = "bottle_holders")
            if _temperature.quantity < 15:
                print("the tempearture is lower than 15 and can not be reached on the platform. the user should place it somewhere else.")
                self.logger.warning("the tempearture is lower than 15 and can not be reached on the platform. the user should place it somewhere else.")
                
            if (next_step == None) and (_duration != None) and (_duration.quantity >= 12*3600):
                end_time = str(datetime.now() + timedelta(seconds = _duration.quantity))
                content = f"send the email to the user and ask to collect sample at {end_time}"
                self.mail_sender.send_message(self.task_name, content)
                self.logger.warning(content)
                return 
            
        # else place the bottle to the heating mantle
        else:
            # tune the temperature of the hotplate so that it reaches the desired temperature 
            # if the temperature is None, do nothing
            if temperature == None:
                pass
            else:
                if not temperature: # if temperature is False, turn it off
                    self.hotplate_op.hotplate.turn_heater_off()
                else: # if it is a value, set the temperature
                    self.hotplate_op.hotplate.set_temp(temperature)
                    self.hotplate_op.hotplate.turn_heater_on()
                    time.sleep(10*60)
            # wait for 10 minutes to reach the temperature, and we will keep it there
            
            # then place the vial there 
            self._adjust_temperature_for_vial(
                reactor = _reactor_name, 
                temperature = temperature, 
                stir_speed = stir_speed, 
                open_bottle = True)
            
            # wait for 10 minutes to reach the temperature, and we will keep it there
            if temperature is not None:
                time.sleep(10*60)

        time.sleep(duration)

    def perform_exp(self):
        """
        Start experiment desigined by NL model.
        
        """
        # prepare liquids for the experiment
        for function in self.parsed_functions:
            if type(function) not in self.supported_types:
                raise ValueError("function not suporrted!")
            
        for function in self.parsed_functions:
            if type(function) == llmlab.operations.exp_operation.AdjustpH:
                self.pH_test_op.initialize_pH_sys()
                self.liquid_station._calibrate_pHmeter()
                break
        
        functions_to_execute = [function for function in self.parsed_functions if (type(function) != llmlab.operations.exp_operation.Yield)]

        self.prepare_solid(solid_prepare_procedure = self.solid_prepare_procedure)
        self.prepare_liquid(liquid_prepare_procedure = self.liquid_prepare_procedure)

        for idx in range(len(functions_to_execute)):
            if idx < len(functions_to_execute) - 1:
                self.perform_one_step(functions_to_execute[idx], functions_to_execute[idx + 1])
            else:
                self.perform_one_step(functions_to_execute[idx], None)

    def perform_one_step(self, 
                         function: llmlab.operations.exp_operation.BasicStep, 
                         next_step: llmlab.operations.exp_operation.BasicStep):
        """
        perform the synthesis step.
        Args: 
            function: the function.
            next_step: the next function.
        """
        if type(function) == llmlab.operations.exp_operation.AddLiquid:
            print(f"task: {self.AddLiquid.__name__} start, now time is {datetime.now()}")
            self.AddLiquid(function, next_step)
            print(f"task: {self.AddLiquid.__name__} over, now time is {datetime.now()}")
        if type(function) == llmlab.operations.exp_operation.AddSolid:
            print(f"task: {self.AddSolid.__name__} start, now time is {datetime.now()}")
            self.AddSolid(function, next_step)
            print(f"task: {self.AddSolid.__name__} over, now time is {datetime.now()}")
        elif type(function) == llmlab.operations.exp_operation.AdjustTemperatureTo:
            print(f"task: {self.AdjustTemperatureTo.__name__} start, now time is {datetime.now()}")
            self.AdjustTemperatureTo(function, next_step)
            print(f"task: {self.AdjustTemperatureTo.__name__} over, now time is {datetime.now()}")
        elif type(function) == llmlab.operations.exp_operation.AdjustTemperatureForDuration:
            print(f"task: {self.AdjustTemperatureForDuration.__name__} start, now time is {datetime.now()}")
            self.AdjustTemperatureForDuration(function, next_step)
            print(f"task: {self.AdjustTemperatureForDuration.__name__} over, now time is {datetime.now()}")
        elif type(function) == llmlab.operations.exp_operation.Wait:
            print(f"task: {self.Wait.__name__} start, now time is {datetime.now()}")
            self.Wait(function, next_step)
            print(f"task: {self.Wait.__name__} over, now time is {datetime.now()}")
        elif type(function) == llmlab.operations.exp_operation.TransferLiquid:
            print(f"task: {self.TrasnferLiquid.__name__} start, now time is {datetime.now()}")
            self.TrasnferLiquid(function, next_step)
            print(f"task: {self.TrasnferLiquid.__name__} over, now time is {datetime.now()}")
        elif type(function) == llmlab.operations.exp_operation.Precipitate:
            print(f"task: {self.Precipitate.__name__} start, now time is {datetime.now()}")
            self.Precipitate(function, next_step)
            print(f"task: {self.Precipitate.__name__} over, now time is {datetime.now()}")
        elif type(function) == llmlab.operations.exp_operation.StirForDuration:
            print(f"task: {self.StirForDuration.__name__} start, now time is {datetime.now()}")
            self.StirForDuration(function, next_step)
            print(f"task: {self.StirForDuration.__name__} over, now time is {datetime.now()}")
        elif type(function) == llmlab.operations.exp_operation.StartStir:
            print(f"task: {self.StartStir.__name__} start, now time is {datetime.now()}")
            self.StartStir(function, next_step)
            print(f"task: {self.StartStir.__name__} over, now time is {datetime.now()}")
        elif type(function) == llmlab.operations.exp_operation.StopStir:
            print(f"task: {self.StopStir.__name__} start, now time is {datetime.now()}")
            self.StopStir(function, next_step)
            print(f"task: {self.StopStir.__name__} over, now time is {datetime.now()}")
        elif type(function) == llmlab.operations.exp_operation.WashSolid:
            print(f"task: {self.WashSolid.__name__} start, now time is {datetime.now()}")
            self.WashSolid(function, next_step)
            print(f"task: {self.WashSolid.__name__} over, now time is {datetime.now()}")
        elif type(function) == llmlab.operations.exp_operation.Filter:
            print(f"task: {self.Filter.__name__} start, now time is {datetime.now()}")
            self.Filter(function, next_step)
            print(f"task: {self.Filter.__name__} over, now time is {datetime.now()}")
        elif type(function) == llmlab.operations.exp_operation.Dry:
            print(f"task: {self.Dry.__name__} start, now time is {datetime.now()}")
            self.Dry(function, next_step)
            print(f"task: {self.Dry.__name__} over, now time is {datetime.now()}")
        elif type(function) == llmlab.operations.exp_operation.AdjustpH:
            print(f"task: {self.AdjustpH.__name__} start, now time is {datetime.now()}")
            self.AdjustpH(function, next_step)
            print(f"task: {self.AdjustpH.__name__} over, now time is {datetime.now()}")
        elif type(function) == llmlab.operations.exp_operation.Evaporate:
            print(f"task: {self.Evaporate.__name__} start, now time is {datetime.now()}")
            self.Evaporate(function, next_step)
            print(f"task: {self.Evaporate.__name__} over, now time is {datetime.now()}")

    def prepare_reactors(self):
        """
        Read the reactors that will be used in the process.
        """

        # get the free vials from solid/liquid stations
        set1 = ["reactor_name", "from_reactor", "to_reactor", "centrifuge_reactor"]
        set2 = ["filtrate_vessel", "waste_vessel"]
        vials_to_use = copy(self.current_mapping["LiquidStation"]["Vials"])
        vials_to_use.update(self.current_mapping["SolidStation"]["Vials"])
        vials_to_use = list(vials_to_use.keys())
        # remove the reactors with solutions (which we should not use them)
        for reactor in self.reactor_with_sol:
            try:
                vials_to_use.remove(reactor)
            except:
                pass

        # pick up the vials that are not used in the functions directly
        free_vials_to_use = [i for i in vials_to_use if i not in self.nl_manager.required_reactors]
        # find all the vials that are used in the function, but does not appear on the platform
        reactors_to_find_= []
        for func in self.parsed_functions:
            for key_temp in set1 + set2:
                if hasattr(func, key_temp):
                    current_reactor = getattr(func, key_temp) 
                    if current_reactor not in vials_to_use:
                        reactors_to_find_.append(current_reactor)
        reactors_to_find_ = list(np.unique(reactors_to_find_))
        print(reactors_to_find_)

        # ensure there are enough vials to replace the vials used in the function
        assert len(reactors_to_find_) <= len(free_vials_to_use)

        # replace the reactors
        if len(reactors_to_find_)>0:
            # replace all the vials
            for func in self.parsed_functions:
                # must be replaced 
                for key_temp in set1:
                    if hasattr(func, key_temp):
                        current_reactor = getattr(func, key_temp) 
                        if current_reactor not in vials_to_use:
                            idx = reactors_to_find_.index(current_reactor)
                            setattr(func, key_temp, free_vials_to_use[idx])

                # do not need to be replaced if it is called waste
                for key_temp in set2:
                    if hasattr(func, key_temp):
                        current_reactor = getattr(func, key_temp)
                        if (current_reactor not in vials_to_use) and (current_reactor != "waste"):
                            idx = reactors_to_find_.index(current_reactor)
                            setattr(func, key_temp, free_vials_to_use[idx])
        
        self.nl_manager.get_function_set()
        self.nl_manager.extract_reactors()