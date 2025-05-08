import json
import yaml
import logging
import serial
import time
from copy import copy
from solplatform.manager.operations import fs_axis_gripper_op
from solplatform.manager.operations.fs_axis_gripper_op import FS_Axis_Gripper_op
from solplatform.manager.operations.pH_test_op import pH_Test_op
from .utility import *
from zeep import helpers
from typing import Union, Optional
from datetime import datetime
from Dobot_Arms import MG400
from XPR_balance import XPR204
from dh_gripper import Gripper
from Gas_controller import GASAxis
from MS_hotplate import HotPlateController
from zmotion import AxisMotion
from pHTestuino import pHTestMeter
from leadshine_driver import LeadShine_Controller
from runze_driver import SyringePump, SwitchValve, Injector, PeristalticPump
from solplatform.manager.drivers.custom_pump import SyringePump_with_Valve, Valve
from solplatform.manager.operations import (
    MG400_op,
    XPR_balance_op,
    LS_Axis_Gripper_op,
    SyringePump_op,
    HotPlate_op,
    Leadshine_Motor_op,
)
from solplatform.manager.stations import SolidStation, LiquidStation, FiltrationStation


DEFULT_STIR_SPEED = 300


class PlatformManager:

    def __init__(
        self,
        platform_config_path: str,
        solid_station_mapping_path: str,
        liquid_station_mapping_path: str,
        filtration_station_mapping_path: str,
        logger: logging.Logger,
        initialize_operation: bool = True
    ):
        """ 
        Initialize all devices, operations, stations.
        """
        # initialize logger
        self.logger = logger

        # initialize config
        with open(platform_config_path, "r", encoding="utf-8") as file:
            self.config = yaml.safe_load(file)

        # import the devices param on solid station
        self.balance_ip = self.config["SolidStation"]["IO"]["XRP_balance"]["ip"]
        self.MG400_ip = self.config["SolidStation"]["IO"]["MG400"]["ip"]
        self.pgse_connection = serial.Serial(**self.config["SolidStation"]["IO"]["pgse"]["connection_param"])
        # import the dh_devices param on liquidstation
        self.axismotion_connection = self.config["LiquidStation"]["IO"]["axismotion"]
        self.gripper_connection = serial.Serial(**self.config["LiquidStation"]["IO"]["grippers"]["connection_param"])
        # import the runze devices param on liquidstation
        self.runze_0_connection = serial.Serial(**self.config["LiquidStation"]["IO"]["runze_0"]["connection_param"])
        self.runze_0_config = self.config["LiquidStation"]["IO"]["runze_0"]["config_param"]
        self.runze_0_channels = self.config["LiquidStation"]["IO"]["runze_0"]["channels"]
        self.injector_connection = serial.Serial(**self.config["LiquidStation"]["IO"]["injector"]["connection_param"])
        self.injector_config = self.config["LiquidStation"]["IO"]["injector"]["config_param"]
        self.runze_1_connection = serial.Serial(**self.config["LiquidStation"]["IO"]["runze_1"]["connection_param"])
        self.runze_1_config = self.config["LiquidStation"]["IO"]["runze_1"]["config_param"]

        self.hotplate_connection = serial.Serial(**self.config["LiquidStation"]["IO"]["hotplate"]["connection_param"])
        
        self.pHmeter_port = self.config["LiquidStation"]["IO"]["pHmeter"]["port"]
        self.LS_bopai_controller_param = self.config["LiquidStation"]["IO"]["bopai_controller"]
        
        # import the devices param on filtration
        self.fs_axis_motion_param = self.config["FiltrationStation"]["IO"]["bopai_controller"]
        self.fs_switch_valve_connection = serial.Serial(**self.config["FiltrationStation"]["IO"]["fs_switch_valve"]["connection_param"])
        self.fs_switch_valve_config = self.config["FiltrationStation"]["IO"]["fs_switch_valve"]["config_param"]
        self.fs_switch_valve_channels = self.config["FiltrationStation"]["IO"]["fs_switch_valve"]["channels"]
        self.fs_switch_valve_solvent_factor = self.config["FiltrationStation"]["IO"]["fs_switch_valve"]["solvent_factor"]
        self.rgi100_connection = serial.Serial(**self.config["FiltrationStation"]["IO"]["rgi100"]["connection_param"])

        # import the leadshine motor param
        self.motor_0_connection = serial.Serial(**self.config["LeadShineMotor"]["IO"]["SS_LS"]["connection_param"])
        self.motor_0_param = self.config["LeadShineMotor"]["IO"]["SS_LS"]["motion_param"]
        self.motor_1_connection = serial.Serial(**self.config["LeadShineMotor"]["IO"]["LS_FS"]["connection_param"])
        self.motor_1_param = self.config["LeadShineMotor"]["IO"]["LS_FS"]["motion_param"]
        # import initial slave params
        self.slave = {}
        for pump_name in self.runze_0_config.keys():
            self.slave[pump_name] = self.runze_0_config[pump_name]["slave"]
        for pump_name in self.runze_1_config.keys():
            self.slave[pump_name] = self.runze_1_config[pump_name]["slave"]
        for gripper_name in self.config["LiquidStation"]["IO"]["grippers"]["slave_param"].keys():
            self.slave[gripper_name] = self.config["LiquidStation"]["IO"]["grippers"]["slave_param"][gripper_name]
        self.slave["injector"] = self.injector_config['slave']
        self.slave["fs_switch_valve"] = self.fs_switch_valve_config["slave"]
        self.slave["pgse"] = self.config["SolidStation"]["IO"]["pgse"]["slave_param"]
        self.slave["rgi100"] = self.config["FiltrationStation"]["IO"]["rgi100"]["slave_param"]
        self.slave["motor_0"] = self.config["LeadShineMotor"]["IO"]["SS_LS"]["slave_param"]
        self.slave["motor_1"] = self.config["LeadShineMotor"]["IO"]["LS_FS"]["slave_param"]
        
        # initialize coordinates
        self.liquid_coordinates = self.config["LiquidStation"]["coordinates"]
        self.solid_coordinates = self.config["SolidStation"]["coordinates"]
        self.filtration_coordinates = self.config["FiltrationStation"]["coordinates"]
        self.leadshine_coordinates = self.config["LeadShineMotor"]["coordinates"]

        self.liquidstation_info = self.config["LiquidStation"]["info"]
        # initialize the capacity of holders
        self.plate_0_capacity = self.solid_coordinates["MG400"]["Holder_Param"]["plate_0"][1][1]
        self.plate_1_capacity = self.solid_coordinates["MG400"]["Holder_Param"]["plate_1"][1][1]
        self.bottle_holder_capacity = (
            self.liquidstation_info["bottle_holders"]["info"][0]
            * self.liquidstation_info["bottle_holders"]["info"][1]
        )
        self.heater_capacity = (
            self.liquidstation_info["heat_bottle_holders"]["info"][0]
            * self.liquidstation_info["heat_bottle_holders"]["info"][1]
        )

        # initialize the offsets
        # self.offsets = self.config["LiquidStation"]["IO"]["offsets"]

        # initialize plates
        self.solidstation_plates = self.config["SolidStation"]["plates"]
        self.liquidstation_plates = self.config["LiquidStation"]["plates"]
        self.filtrationstation_plates = self.config["FiltrationStation"]["plates"]

        # initialize mapping
        self.solid_station_mapping_path = solid_station_mapping_path
        with open(self.solid_station_mapping_path, "r") as file:
            self.SS_mapping = json.load(file)
        self.SS_storage_mapping = self.SS_mapping["Storage"]
        self.SS_current_mapping = self.SS_mapping["Current"]

        self.liquid_station_mapping_path = liquid_station_mapping_path
        with open(self.liquid_station_mapping_path, "r") as file:
            self.LS_mapping = json.load(file)
        self.LS_storage_mapping = self.LS_mapping["Storage"]
        self.LS_current_mapping = self.LS_mapping["Current"]

        self.filtration_station_mapping_path = filtration_station_mapping_path
        with open(self.filtration_station_mapping_path, "r") as file:
            self.FS_mapping = json.load(file)
        self.FS_storage_mapping = self.FS_mapping["Storage"]
        self.FS_current_mapping = self.FS_mapping["Current"]

        self.current_mapping = {}
        self.current_mapping["SolidStation"] = self.SS_current_mapping
        self.current_mapping["LiquidStation"] = self.LS_current_mapping
        self.current_mapping["FiltrationStation"] = self.FS_current_mapping
        self.current_mapping["Solutions"] = {}
        self.current_mapping["Solids"] = {}

        self.storage_mapping = {}
        self.storage_mapping["SolidStation"] = self.SS_storage_mapping
        self.storage_mapping["LiquidStation"] = self.LS_storage_mapping
        self.storage_mapping["FiltrationStation"] = self.FS_storage_mapping
        self.storage_mapping["Solutions"] = {}
        self.storage_mapping["Solids"] = {}

        # initialize devices
        self.devices = {}
        self.devices["XPR_balance"] = XPR204(
            self.balance_ip, 
            logger=self.logger
        )
        self.devices["MG400"] = MG400(
            self.MG400_ip, 
            logger=self.logger
        )
        self.devices["Axismotion"] = AxisMotion(
            self.axismotion_connection, 
            self.logger
        )
        self.devices["rgi30"] = Gripper(
            self.gripper_connection, 
            self.slave["rgi30"], 
            self.logger, 
            "rgi30"
        )
        self.devices["pge50"] = Gripper(
            self.gripper_connection, 
            self.slave["pge50"], 
            self.logger, 
            "pge50"
        )
        self.devices["rgi100"] = Gripper(
            self.rgi100_connection, 
            self.slave["rgi100"], 
            self.logger, 
            "rgi100"
        )
        self.devices["pgse"] = Gripper(
            self.pgse_connection, 
            self.slave["pgse"], 
            self.logger, 
            "pgse"
        )
        self.devices["Injector"] = Injector(
            self.injector_connection,
            self.slave["injector"],
            self.injector_config["model"], 
            self.injector_config["tip_volume"],
            self.injector_config["max_volume"], 
            self.logger
        )
        # initialize runze_0 devices
        self.devices["SyringePump"] = SyringePump(
            self.runze_0_connection, 
            self.slave["syringe_pump"], 
            self.runze_0_config["syringe_pump"]["model"], 
            self.runze_0_config["syringe_pump"]["max_volume"], 
            self.logger
        )
        self.devices["SwitchValve"] = SwitchValve(
            self.runze_0_connection, 
            self.slave["switch_valve"], 
            self.runze_0_config["switch_valve"]["channel_num"],
            self.runze_0_config["switch_valve"]["model"],  
            self.logger
        )
        # initialize the runze_1 devices
        self.devices["valve_acid"] = Valve(
            self.devices["Axismotion"], 
            "valve_acid"
        )
        self.devices["valve_base"] = Valve(
            self.devices["Axismotion"], 
            "valve_base"
        )
        for device_name in list(self.runze_1_config.keys())[:2]:
            self.devices[device_name] = SyringePump(
                self.runze_1_connection, 
                self.slave[device_name], 
                self.runze_1_config[device_name]['model'], 
                self.runze_1_config[device_name]['max_volume'], 
                self.logger
            )
        self.devices["pump_acid"] = SyringePump_with_Valve(
            self.devices["pump_acid"], 
            self.devices["valve_acid"], 
            self.logger
        )
        self.devices["pump_base"] = SyringePump_with_Valve(
            self.devices["pump_base"], 
            self.devices["valve_base"], 
            self.logger
        )
        for device_name in list(self.runze_1_config.keys())[2:]:
            self.devices[device_name] = PeristalticPump(
                self.runze_1_connection, 
                self.slave[device_name], 
                self.logger
            )
        self.devices["pHmeter"] = pHTestMeter(
            self.pHmeter_port, 
            self.logger
        )
        self.devices["HotPlate"] = HotPlateController(
            self.hotplate_connection, 
            self.logger
        )
        self.devices["fs_axis"] = GASAxis(
            self.fs_axis_motion_param, 
            self.logger
        )
        self.devices["fs_switch_valve"] = SwitchValve(
            self.fs_switch_valve_connection, 
            self.slave["fs_switch_valve"], 
            self.fs_switch_valve_config["channel_num"], 
            self.fs_switch_valve_config["model"], 
            self.logger
        )
        self.devices["motor_0"] = LeadShine_Controller(
            self.motor_0_connection,
            self.slave["motor_0"],
            self.motor_0_param,
            self.logger
        )
        self.devices["motor_1"] = LeadShine_Controller(
            self.motor_1_connection,
            self.slave["motor_1"],
            self.motor_1_param,
            self.logger
        )
        
        # initialize the bopai controller of LS
        self.devices["LS_pH_multi_axis"] = GASAxis(self.LS_bopai_controller_param, self.logger)
        
        # add lock for the devices
        for device in self.devices.values():
            add_lock(device)
        # initialize operations of devices
        if initialize_operation:
            self.XPR_balance_op = XPR_balance_op(
                balance=self.devices["XPR_balance"], logger=self.logger
            )

            self.MG400_op = MG400_op(
                mg400 = self.devices["MG400"],
                pgse = self.devices["pgse"],
                coordinates = self.solid_coordinates["MG400"],
                logger = self.logger,
            )
            
            self.pH_test_op = pH_Test_op(
                self.devices["pHmeter"], 
                self.devices["pump_waste"], 
                self.devices["pump_water"], 
                self.devices["pump_KCl"], 
                self.devices["pump_acid"], 
                self.devices["pump_base"], 
                self.devices["LS_pH_multi_axis"],
                self.logger
            )
            
            self.ls_axis_gripper_op = LS_Axis_Gripper_op(
                axismotion = self.devices["Axismotion"],
                rgi30 = self.devices["rgi30"],
                pge50 = self.devices["pge50"],
                injector = self.devices["Injector"],
                config = self.config["LiquidStation"],
                logger = self.logger,
            )

            self.syringepump_op = SyringePump_op(
                syringe_pump=self.devices["SyringePump"],
                switch_valve=self.devices["SwitchValve"],
                syringe_pump_channels = self.runze_0_channels["syringe_pump"],
                switch_valve_channels = self.runze_0_channels["switch_valve"],
                logger=self.logger
            )
            
            self.hotplate_op = HotPlate_op(
                hotplate=self.devices["HotPlate"], 
                logger=self.logger
            )
            self.fs_axis_gripper_op = FS_Axis_Gripper_op(
                self.devices["fs_axis"], 
                self.devices["rgi100"], 
                self.devices["fs_switch_valve"], 
                self.filtration_coordinates, 
                self.fs_switch_valve_channels, 
                self.fs_switch_valve_solvent_factor, 
                self.logger
            )
            self.moving_stage_op = Leadshine_Motor_op(
                self.devices["motor_0"], 
                self.devices["motor_1"], 
                logger=self.logger
            )

            self.operations = {}
            self.operations["XPR_balance_op"] = self.XPR_balance_op
            self.operations["MG400_op"] = self.MG400_op
            self.operations["Axis_Gripper_op"] = self.ls_axis_gripper_op
            self.operations["SyringePump_op"] = self.syringepump_op
            self.operations["pH_Test_op"] = self.pH_test_op
            self.operations["HotPlate_op"] = self.hotplate_op
            self.operations["FS_Axis_Gripper_op"] = self.fs_axis_gripper_op
            self.operations["Motor_op"] = self.moving_stage_op
            

            for operation in self.operations.values():
                add_lock(operation)

            # Initialize environment
            env = PHAdjustmentEnv()

            self.liquid_station = LiquidStation(
                axis_gripper_op = self.ls_axis_gripper_op,
                syringepump_op = self.syringepump_op,
                hotplate_op = self.hotplate_op,
                moving_stage_op = self.moving_stage_op,
                pH_test_op = self.pH_test_op, 
                uv_vis_setup = self.uv_vis_setup,
                pH_adjust_env= env, 
                mapping = self.LS_mapping,
                storage_mapping = self.LS_storage_mapping,
                current_mapping = self.LS_current_mapping,
                info = self.liquidstation_info,
                logger = self.logger,
            )

            self.solid_station = SolidStation(
                XPR_balance_op = self.XPR_balance_op,
                MG400_op = self.MG400_op,
                moving_stage_op = self.moving_stage_op,
                mapping = self.SS_mapping,
                storage_mapping = self.SS_storage_mapping,
                current_mapping = self.SS_current_mapping,
                coordinates = self.solid_coordinates,
                logger = self.logger
            )
            self.filtration_station = FiltrationStation(
                axis_gripper_op = self.fs_axis_gripper_op, 
                leadshine_motor_op = self.moving_stage_op, 
                storage_mapping = self.FS_storage_mapping, 
                current_mapping = self.FS_current_mapping, 
                coordinates = self.filtration_coordinates, 
                logger = self.logger
            )
            add_lock(self.liquid_station)
            add_lock(self.solid_station)
            add_lock(self.filtration_station)
    

    def motor_move(self, motor_idx: int, target_position: float):
        """
        Control the motion of motor (Leadshine).

        Args:
            motor_idx: the index of motor.
            target_position: the taget position, mm.
        """
        if self.moving_stage_op.current_position[motor_idx] == target_position:
            return True
        else:
            axis_pos = self.ls_axis_gripper_op.axismotion.read_position()
            if axis_pos[0] == self.liquid_coordinates[f"motor_{motor_idx}_ls"][0][0]:
                self.ls_axis_gripper_op._reset_axis_z()
            self.moving_stage_op.move_to_position(motor_idx, target_position)

    def search_reactor_location(self, reactor):
        """
        Get the current reactor location
        
        Args: 
            reactor: get the information of the selected reactor.
        """
        for station in self.current_mapping.values():
            if reactor in station["Vials"]:
                vial_info = station["Vials"][reactor]
                return vial_info
            
    def move_vial_within_liquidstation(self, reactor: str, target_plate: str, target_idx: int = 0):
        """
        Move Vial to the target place on the liquid station.

        Args:
            reactor: the name of vail.
            target_plate: the name of target place.
            target_idx: the index of position. Defaults to 0.
        """
        # find the current location of the reactor
        vial_info = self.LS_current_mapping["Vials"][reactor]
        # make sure the bottle is on liquidstation
        if vial_info["bottle_plate"] in self.liquidstation_plates:
            # if the bottle is already in the target place, do nothing
            if (vial_info["bottle_plate"] == target_plate and vial_info["slot_index"] == target_idx):
                return True
            else:
                # move the moving stage to liquidstation if needed
                if "motor_0_ls" in [vial_info["bottle_plate"], target_plate]:
                    if check_obj_status("vial", "motor_0_ss", target_idx, self.SS_current_mapping):
                        raise ValueError("The motor_0 is full!")
                    self.motor_move(0, self.leadshine_coordinates["motor_0"])
                # move the moving stage to liquidstation if needed
                if "motor_1_ls" in [vial_info["bottle_plate"], target_plate]:
                    if check_obj_status("vial", "motor_1_fs", target_idx, self.FS_current_mapping):
                        raise ValueError(f"The motor_1 with index: {target_idx} is full!")
                    self.motor_move(1, 0)       
                # if the target locaiton is not empty, raise error
                if (check_obj_status("vial", target_plate, target_idx, self.LS_current_mapping) and target_plate != "rubbish_bin"):
                    raise ValueError(f"{target_plate} with index of {target_idx} is occupied!")
                
                # pick up the bottle, the z_offset will be different according to the cappting status
                if not vial_info["capped"]:
                    z1_offset = 0
                else:
                    z1_offset = 0
                self.ls_axis_gripper_op._get_obj(vial_info["bottle_plate"], vial_info["slot_index"], z1_offset)
                # place the bottle
                self.ls_axis_gripper_op._place_obj(target_plate, target_idx, z1_offset=z1_offset)
                # update graph
                if (self.LS_current_mapping["Vials"][reactor]["bottle_plate"] == "heat_bottle_holders"):
                    self.LS_current_mapping["Vials"][reactor]["temperature"] = False
                    self.LS_current_mapping["Vials"][reactor]["stir"] = False
                self.LS_current_mapping["Vials"][reactor]["bottle_plate"] = target_plate
                self.LS_current_mapping["Vials"][reactor]["slot_index"] = target_idx
                # if the destination is hot plate, assign the temperature and stirring speed to the vial 
                if target_plate == "heat_bottle_holders":
                    self.LS_current_mapping["Vials"][reactor]["temperature"] = self.hotplate_op.hotplate.target_temp
                    self.LS_current_mapping["Vials"][reactor]["stir"] = self.hotplate_op.hotplate.target_stir
        else:
            raise ValueError("current vial is not on liquid station!")

    def move_vial_within_solidstation(self, reactor: str, target_plate: str, target_idx: int = 0):
        """
        Move Vial to the target place on the solid station.

        Args:
            reactor: the name of vail.
            target_plate: the name of target place.
            target_idx: the index of position. Defaults to 0.
        """
        # find the current location of the reactor
        vial_info = self.SS_current_mapping["Vials"][reactor]
        # make sure the bottle is on solidstation
        if vial_info["bottle_plate"] in self.solidstation_plates:
            # if the bottle is already in the target place
            if (vial_info["bottle_plate"] == target_plate and vial_info["slot_index"] == target_idx):
                return True
            else:
                # home the moving stage if needed
                if "motor_0_ss" in [vial_info["bottle_plate"], target_plate]:
                    if check_obj_status("vial", "motor_0_ls", target_idx, self.LS_current_mapping):
                        raise ValueError("The motor_0 is full!")
                    self.motor_move(0, 0)
                # make sure the target place is empty
                if check_obj_status("vial", target_plate, target_idx, self.SS_current_mapping):
                    raise ValueError(f"{target_plate} with index of {target_idx} is occupied!")
                
                # move within the solid station
                # open the balance door if needed
                if "balance" in [vial_info["bottle_plate"], target_plate]:
                    self.XPR_balance_op.open_door()
                # move the vial into the target slot
                if (vial_info["bottle_plate"] == "balance") and (target_plate in["plate_0","plate_1"]):
                    # pick up from the balance and move it to the plate
                    self.MG400_op.bottle_balance_to_plate(target_plate, target_idx)
                    
                elif (vial_info["bottle_plate"] in ["plate_0","plate_1"]) and (target_plate == "balance"):
                    # pick up from the plate and move it to the balance
                    self.MG400_op.bottle_plate_to_balance(vial_info["bottle_plate"], vial_info["slot_index"])
                    
                elif (vial_info["bottle_plate"] in ["plate_0", "plate_1"]) and (target_plate == "motor_0_ss"):
                    # pick up from the plate and move it to the liquid station initial point
                    self.MG400_op.bottle_plate_to_LS(vial_info["bottle_plate"], vial_info["slot_index"])
                    
                elif (vial_info["bottle_plate"] == "balance") and (target_plate == "motor_0_ss"):
                    # pick up from the balance and move it to the liquid station initial point
                    self.MG400_op.bottle_balance_to_LS()
                    
                elif (vial_info["bottle_plate"] == "motor_0_ss") and (target_plate in ["plate_0", "plate_1", "balance"]):
                    # pick up from the liquid station initial point and move it to the balance or plate
                    self.MG400_op.bottle_LS_to_plate_or_balance(target_plate, target_idx)
                    
                elif (vial_info["bottle_plate"] in ["plate_0","plate_1"]) and (target_plate in ["plate_0", "plate_1"]):
                    # transfer within the plates
                    self.MG400_op.bottle_plate_to_plate(vial_info["bottle_plate"], vial_info["slot_index"], target_plate, target_idx)
                else:
                    raise ValueError("unsupported transfer within solid station!")

                # update the graph
                self.SS_current_mapping["Vials"][reactor]["bottle_plate"] = target_plate
                self.SS_current_mapping["Vials"][reactor]["slot_index"] = target_idx
                # reset the temperature and stirring speed
                self.SS_current_mapping["Vials"][reactor]["temperature"] = False
                self.SS_current_mapping["Vials"][reactor]["stir"] = False
                
        else:
            raise ValueError("current vial is not on solid station!")

    def move_vial_within_filrationstation(self, reactor: str, target_plate: str, target_idx: int):
        """
        Transfer a reactor in the solidstation to motor_0 or other holder on liquidstation.
        or if the reactor is already inside the liquidstation, raise error.
        Args:
            reactor: the name of the reactor
            target_plate: the name of target place.
            target_idx: the index of position.
        """
        # 
        vial_info = self.search_reactor_location(reactor)
        if vial_info["bottle_plate"] in self.filtrationstation_plates:
            if (vial_info["bottle_plate"] == target_plate and vial_info["slot_index"] == target_idx):
                return True
            else:
                self.filtration_station.move_bottle_to(vial_info["slot_index"], target_idx)
                self.FS_current_mapping["Vials"][reactor]["bottle_plate"] = target_plate
                self.FS_current_mapping["Vials"][reactor]["slot_index"] = target_idx            
        else:
            raise ValueError("vial is not on the filtrationstation!")

    def solidstation_to_liquidstation(self, reactor, target_plate: str = "motor_0_ls", target_idx: int = 0):
        """
        Transfer a reactor in the solidstation to motor_0 or other holder on liquidstation.
        or if the reactor is already inside the liquidstation, raise error.
        Args:
            reactor: the name of the reactor
            target_plate: the name of target place.
            target_idx: the index of position.
        """
        # find the current location of the reactor
        vial_info = self.search_reactor_location(reactor)
        # check if the reactor is on solidstation
        if vial_info["bottle_plate"] in self.solidstation_plates:
            # place the vial into the moving stage
            self.move_vial_within_solidstation(reactor, "motor_0_ss")
            self.motor_move(0, self.leadshine_coordinates["motor_0"])
            # update the caps
            cap_on_bottle = self.SS_current_mapping["Vials"][reactor]["capped"]
            if cap_on_bottle:
                self.LS_current_mapping["Caps"][cap_on_bottle] = (self.SS_current_mapping["Caps"].pop(cap_on_bottle))
            self.LS_current_mapping["Vials"][reactor] = self.SS_current_mapping["Vials"].pop(reactor)
            self.LS_current_mapping["Vials"][reactor]["bottle_plate"] = "motor_0_ls"
            # place the vial into the target slot on liquidstation
            self.move_vial_within_liquidstation(reactor, target_plate, target_idx)
        else:
            raise ValueError("vial is not on the solidstation!")

    def liquidstation_to_solidstation(self, reactor: str, target_plate: str = "motor_0_ss", target_idx: int = 0):
        """
        Transfer a reactor in the liquidstation to solidstation(motor_0) or other holder on solidstation.
        or if the reactor is already inside the solidstation, raise error.
        Args:
            reactor: the name of the reactor
            plate_name: the target plate name of the solid station
            target_idx: the slot index of the target plate that we will move the reactor to
        """
        # get the information of the vial
        vial_info = self.search_reactor_location(reactor)
        # check if the vial is in liquid_station
        if vial_info["bottle_plate"] in self.liquidstation_plates:
            # place the vial into the moving stage
            self.move_vial_within_liquidstation(reactor, "motor_0_ls")
            # if it is motor_0, the information will be popped to the solid station config
            self.motor_move(0, 0)
            cap_on_bottle = self.LS_current_mapping["Vials"][reactor]["capped"]
            if cap_on_bottle:
                self.SS_current_mapping["Caps"][cap_on_bottle] = (self.LS_current_mapping["Caps"].pop(cap_on_bottle))
            self.SS_current_mapping["Vials"][reactor] = self.LS_current_mapping["Vials"].pop(reactor)
            self.SS_current_mapping["Vials"][reactor]["bottle_plate"] = "motor_0_ss"
            # place the vial into the target slot on solidstation
            self.move_vial_within_solidstation(reactor, target_plate, target_idx)
        else:
            raise ValueError("vial is not on the liquidstation!")
        
    def liquidstation_to_filtrationstation(self, vial: str, target_plate: str = 'motor_1_fs', target_idx: int = 0):
        """
        Move the vial from liquid station to filtration station.
        Args:
            reactor: the name of the reactor
            plate_name: the target plate name of the solid station
            target_idx: the slot index of the target plate that we will move the reactor to
        """
        # get the information of the vial
        vial_info = self.search_reactor_location(vial)
        # make sure the vial is on the liquid station
        if vial_info["bottle_plate"] in self.liquidstation_plates:
            # place the vial into the moving stage
            self.move_vial_within_liquidstation(vial, 'motor_1_ls', target_idx)
            self.motor_move(1, self.leadshine_coordinates['motor_1'])
            # update the graph from liquid station
            vials_on_motor = []
            for vial in self.LS_current_mapping["Vials"]:
                if self.LS_current_mapping["Vials"][vial]["bottle_plate"] == "motor_1_ls": 
                    vials_on_motor.append(vial)
            for vial in vials_on_motor:
                cap_on_bottle = self.LS_current_mapping["Vials"][vial]["capped"]
                if cap_on_bottle:
                    self.FS_current_mapping["Caps"][cap_on_bottle] = (self.LS_current_mapping["Caps"].pop(cap_on_bottle))
                self.FS_current_mapping["Vials"][vial] = self.LS_current_mapping["Vials"].pop(vial)
                self.FS_current_mapping["Vials"][vial]["bottle_plate"] = "motor_1_fs"
        else:
            raise ValueError("vial is not on the liquidstation!")

    def filtrationstation_to_liquidstation(self, reactor: str, target_plate: str, target_idx: int):
        """
        Move the vial from filtration station to liquid station.
        Args:
            reactor: the name of the reactor
            plate_name: the target plate name of the solid station
            target_idx: the slot index of the target plate that we will move the reactor to
        """
        # get the information of the vial 
        vial_info = self.search_reactor_location(reactor)
        # make sure the vial is on the filtration station
        if vial_info["bottle_plate"] in self.filtrationstation_plates:
            # home the moving stage the liquid station
            self.motor_move(1, 0)
            # update the graph from filtration station (it is in liquid station now)
            vials_on_motor = []
            for vial in self.FS_current_mapping["Vials"]:
                if self.FS_current_mapping["Vials"][vial]["bottle_plate"] == "motor_1_fs": 
                    vials_on_motor.append(vial)
            for vial in vials_on_motor:
                cap_on_bottle = self.FS_current_mapping["Vials"][vial]["capped"]
                if cap_on_bottle:
                    self.LS_current_mapping["Caps"][cap_on_bottle] = (self.FS_current_mapping["Caps"].pop(cap_on_bottle))
                self.LS_current_mapping["Vials"][vial] = self.FS_current_mapping["Vials"].pop(vial)
                self.LS_current_mapping["Vials"][vial]["bottle_plate"] = "motor_1_ls"
                # place the vial to the liquid station
            self.move_vial_within_liquidstation(reactor, target_plate, target_idx)
        else:
            raise ValueError("vial is not on the liquidstation!")

    def move_vial_to_target_destination(self, reactor: str, target_plate: str, target_idx: int = 0):
        """
        Move vial within the whole platform contaning multiple workstations.
        Args:
            reactor: the name of the vial
            target_plates: the target plate name
            target_idx: the index of the slot in the target plate
        """
        # get the current location of the vial
        vial_info = self.search_reactor_location(reactor)
        # move the vial into the target slot
        # handle the movement within the same station
        if (vial_info["bottle_plate"] in self.solidstation_plates) and (target_plate in self.solidstation_plates):
            self.move_vial_within_solidstation(reactor, target_plate, target_idx)
        elif (vial_info["bottle_plate"] in self.liquidstation_plates) and (target_plate in self.liquidstation_plates):
            self.move_vial_within_liquidstation(reactor, target_plate, target_idx)
        # solid to liquid
        elif (vial_info["bottle_plate"] in self.solidstation_plates) and (target_plate in self.liquidstation_plates):
            self.solidstation_to_liquidstation(reactor, target_plate, target_idx)
        # liquid to solid 
        elif (vial_info["bottle_plate"] in self.liquidstation_plates) and (target_plate in self.solidstation_plates):
            self.liquidstation_to_solidstation(reactor, target_plate, target_idx)
        # liquid to filtration
        elif (vial_info["bottle_plate"] in self.liquidstation_plates) and (target_plate in self.filtrationstation_plates):
            self.liquidstation_to_filtrationstation(reactor, target_plate, target_idx)
        # filtration to liquid
        elif (vial_info["bottle_plate"] in self.filtrationstation_plates) and (target_plate in self.liquidstation_plates):
            self.filtrationstation_to_liquidstation(reactor, target_plate, target_idx)
        # solid to filtration
        elif (vial_info["bottle_plate"] in self.solidstation_plates) and (target_plate in self.filtrationstation_plates):
            self.solidstation_to_liquidstation(reactor, "motor_1_ls", target_idx)
            self.liquidstation_to_filtrationstation(reactor, target_plate, target_idx)
        # filtration to solidstation
        elif (vial_info["bottle_plate"] in self.filtrationstation_plates) and (target_plate in self.solidstation_plates):
            self.filtrationstation_to_liquidstation(reactor, "motor_0_ls", 0)
            self.liquidstation_to_solidstation(reactor, target_plate, target_idx)
        elif (vial_info["bottle_plate"] in self.filtrationstation_plates) and (target_plate in self.filtrationstation_plates):
            self.move_vial_within_filrationstation(reactor, target_plate, target_idx)
        else:
            raise ValueError(f"can not move {reactor} to {target_plate} with index {target_idx}")

    def open_bottle(self, reactor: str, to_original_location = False):
        """
        open the reactor if the reactor is closed.
        Args:
            reactor: the name of the vial
        """
        vial_info = copy(self.search_reactor_location(reactor))
        if vial_info["capped"]:
            # place the vial to the pge50_platform
            self.move_vial_to_target_destination(reactor, "pge50_platform")
            # open the reactor and place the cap to the cap holder
            self.liquid_station._open_bottle()
            if to_original_location:
                self.move_vial_to_target_destination(
                    reactor = reactor, 
                    target_plate = vial_info["bottle_plate"], 
                    target_idx = vial_info["slot_index"]
                    )
        else:
            return True

    def close_bottle(self, reactor: str, to_original_location = False):
        """
        close the reactor if the reactor is opened.
        Args:
            reactor: the name of the vial
        """
        vial_info = copy(self.search_reactor_location(reactor))
        if not vial_info["capped"]:
            self.move_vial_to_target_destination(reactor, "pge50_platform")
            self.liquid_station._close_bottle()
            if to_original_location:
                self.move_vial_to_target_destination(
                    reactor = reactor, 
                    target_plate = vial_info["bottle_plate"], 
                    target_idx = vial_info["slot_index"]
                    )
        else:
            return True

    def _add_solid(self, reactor: str, solid: list, quantity: list, tolerance: list, stay: bool = False):
        """
        Dispense solid into a reactor.

        Args:
            reactor: the name of the reactor
            solid: array, the names of the heads of solids
            quantity: array, the mass of the solids in mg
            tolerance: array, the percentage of tolerance of each solids
        """
        for w in quantity:
            if w < 0:
                raise ValueError("Substance weight can not be smaller than 0!")
        
        # open the bottle if capped
        self.open_bottle(reactor)
        # move the vial into balance
        self.move_vial_to_target_destination(reactor, "balance")
        # add solid and get the data of dosing
        raw_data = self.solid_station._add_solid(reactor, solid, quantity, tolerance)
        data = [helpers.serialize_object(data_temp) for data_temp in raw_data]
        # obtain the data
        weight_data = dict(time = str(datetime.now()), reactor = reactor)
        for w_data in data:
            weight_data.update(w_data)
        return weight_data

    def place_bottle_for_addition(self, reactor: str, desired_plate: Optional[str] = None):
        """
        find a place where bottle can be added liquid and open bottle.

        Args:
            reactor: the name of reactor
        """
        # get the old vial information
        vial_info = copy(self.search_reactor_location(reactor = reactor))
        
        original_holder = vial_info["bottle_plate"]
        # if there is not preferred plates at all
        if desired_plate == None:
            if (original_holder == "bottle_holders") or (original_holder == "heat_bottle_holders"):
                # only copy the index won't work. the holder should also be copied.
                original_index = vial_info["slot_index"]
                self.open_bottle(reactor, to_original_location = True)
                return original_holder, original_index
            
            else:
                for idx in range(self.bottle_holder_capacity):
                    if not check_obj_status("vial", "bottle_holders", idx, self.LS_current_mapping):
                        self.open_bottle(reactor)
                        self.move_vial_to_target_destination(reactor, "bottle_holders", idx)
                        return "bottle_holders", idx

                for idx in range(self.heater_capacity):
                    if not check_obj_status("vial", "heat_bottle_holders", idx, self.LS_current_mapping):
                        self.open_bottle(reactor)
                        self.move_vial_to_target_destination(reactor, "heat_bottle_holders", idx)
                        return "heat_bottle_holders", idx
        # if there is a preferred plates to be used
        else:
            # if (original_holder == "bottle_holders") or (original_holder == "heat_bottle_holders"):
            #     # only copy the index won't work. the holder should also be copied.
            #     original_index = vial_info["slot_index"]
            #     self.open_bottle(reactor, to_original_location = True)
            #     return original_holder, original_index
            
            if desired_plate == "bottle_holders":
                if (original_holder == "bottle_holders"):
                    original_index = vial_info["slot_index"]
                    self.open_bottle(reactor, True)
                    return "bottle_holders", original_index
                for idx in range(self.bottle_holder_capacity):
                    if not check_obj_status("vial", "bottle_holders", idx, self.LS_current_mapping):
                        self.open_bottle(reactor)
                        self.move_vial_to_target_destination(reactor, "bottle_holders", idx)
                        return "bottle_holders", idx
                    
            elif desired_plate == "heat_bottle_holders":
                if (original_holder == "heat_bottle_holders"):
                    original_index = vial_info["slot_index"]
                    self.open_bottle(reactor, True)
                    return "heat_bottle_holders", original_index
                for idx in range(self.heater_capacity):
                    if not check_obj_status("vial", "heat_bottle_holders", idx, self.LS_current_mapping):
                        self.open_bottle(reactor)
                        self.move_vial_to_target_destination(reactor, "heat_bottle_holders", idx)
                        return "heat_bottle_holders", idx
                    
        raise ValueError("there is no empty slot for adding liquid!")

    def _add_liquid(self,
                    reactor: str,
                    solution: list,
                    volume: list,
                    target_plate: str,
                    target_idx: int,
                    if_return: bool = True,
                    z1_offset: float = 65,
                    add_speed: float = 1.75):
        """
        Add some kinds of liquid into the reactor.

        Args:
            reactor: the name of the reactor
            solution: array, the names of the solutions
            volume: array, the volume of the solutions in mL
            target_plate: the target plate
            target_idx: the target idx
        """
        for v in volume:
            if v < 0:
                raise ValueError("Volume must not be smaller than 0!")

        self.open_bottle(reactor)
        self.move_vial_to_target_destination(reactor, target_plate, target_idx)
        self.liquid_station._add_liquid(reactor,
                                        solution,
                                        volume,
                                        z1_offset = z1_offset,
                                        add_speed = add_speed,
                                        if_return = if_return,
                                        )
        return True

    def _transfer_liquid(self,
                         reactor_0: str,
                         reactor_1: str,
                         volume: float,
                         target_plate_0: str,
                         target_plate_1: str,
                         slot0: int,
                         slot1: int,
                         mix_method: Optional[str] = None,
                         transfer_speed: float = 5/6,
                         ):
        """
        Transfer volumetric liquid from one reactor to another by injector.

        Args:
            reactor_0: the liquid provider.
            reactor_1: the lqiuid accepter.
            volume: the volume of the solutions in mL
            target_plate_0: the target plate of reactor_0
            slot_0: the target idx of reactor_0
            target_plate_1: the target plate of reactor_1
            slot_1: the target idx of reactor_1
            mix_method: the method of liquid mix
            transfer_speed: the speed of injection
        """
        if volume == 0:
            return True
        elif volume < 0:
            raise ValueError("Volume must not be smaller than 0!")
        # open the bottles and move them to the target plate
        self.open_bottle(reactor_0)
        self.move_vial_to_target_destination(reactor_0, target_plate_0, slot0)
        self.open_bottle(reactor_1)
        self.move_vial_to_target_destination(reactor_1, target_plate_1, slot1)
        # perform the transfer of the liquid after placing the vials
        self.liquid_station._transfer_liquid(reactor_0,
                                             reactor_1,
                                             volume,
                                             transfer_speed = transfer_speed,
                                             mix_method = mix_method)

    def _adjust_temperature_for_vial(self,
                                     reactor: str,
                                     temperature: Union[float, bool, None] = 25,
                                     stir_speed: Union[int, bool, None] = DEFULT_STIR_SPEED,
                                     open_bottle: bool = False):
        """
        Adjust temperature of the reactor and stir it.

        Args:
            reactor: the name of the reactor
            temperature: the target temperature in oC
            stir_speed: the target stir speed in rpm
            open_bottle: the trigger whether open bottle before this function

        Raises:
            ValueError: while the heater is full
        """
        # close the cap of the reactor if necessary
        if open_bottle is not None:
            if open_bottle:
                self.open_bottle(reactor)
            else:
                self.close_bottle(reactor)
        
        # check if the vial is already at the heat_bottle_holders. if so, we use the index directly.
        vial_info = self.search_reactor_location(reactor = reactor)
        if vial_info["bottle_plate"] == "heat_bottle_holders":
            target_idx = vial_info["slot_index"] 
        else:
            # get all the locations to find the bottle
            locations_to_find = list(range(self.heater_capacity))
            # pick up from the locations_to_find to place the vial
            empty = False
            for idx in locations_to_find:
                bottle = check_obj_status("vial", "heat_bottle_holders", idx, self.LS_current_mapping)
                if not bottle:
                    # indicate we got an empty slot to use 
                    empty = True
                    target_idx = idx
                    break
            # if no empty bottle is found, raise ValueError.
            if not empty:
                raise ValueError(f"the heater is full!")
        
        # get the current temperature 
        current_temp = self.hotplate_op.hotplate.target_temp
        current_speed = self.hotplate_op.hotplate.target_stir
        # if the temperature is None, do nothing
        if temperature == None:
            pass
        else:
            if not temperature: # if temperature is False, turn it off
                self.hotplate_op.hotplate.turn_heater_off()
            else: # if it is a value, set the temperature
                self.hotplate_op.hotplate.set_temp(temperature)
                self.hotplate_op.hotplate.turn_heater_on()
                current_temp = self.hotplate_op.hotplate.target_temp
        # if the stirring is None, do nothing 
        if stir_speed == None:
            pass
        else:
            if not stir_speed: # if the stir_speed is False, turn off the stirring
                self.hotplate_op.hotplate.turn_stir_off()
            else: # if it is a value, set up the rpm for the stirring
                self.hotplate_op.hotplate.set_rpm(stir_speed)
                self.hotplate_op.hotplate.turn_stir_on()
                current_speed = self.hotplate_op.hotplate.target_stir

        # if the target temperature(stir_speed) is not equal to current temperature(stir_speed), record warning
        if temperature != current_temp or stir_speed != current_speed:
            self.logger.warning(f"the temperature of the heater is not equal to the target temperature, current temperature is {current_temp} and target temperature is {temperature}")
        # move the reactor to the empty slot
        self.move_vial_to_target_destination(reactor, target_plate = "heat_bottle_holders", target_idx = target_idx)
        # record the temperature(stir_speed) of the bottle on heater
        for idx in range(self.heater_capacity):
            bottle = check_obj_status("vial", "heat_bottle_holders", idx, self.LS_current_mapping)
            if bottle:
                self.LS_current_mapping["Vials"][bottle]["temperature"] = self.hotplate_op.hotplate.target_temp
                self.LS_current_mapping["Vials"][bottle]["stir"] = self.hotplate_op.hotplate.target_stir

