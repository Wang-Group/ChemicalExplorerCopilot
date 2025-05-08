import logging
import time

from sympy import total_degree

from solplatform import manager
from ..operations import LS_Axis_Gripper_op, SyringePump_op, HotPlate_op, Leadshine_Motor_op, pH_Test_op
from ..drivers.uv_vis_setup import UV_vis_setup
from ..operations.pump_op import HIGH_SPEED, MID_SPEED
from ..operations.hotplate_op import DEFAULT_STIR_SPEED
from ..utility import *


class LiquidStation:
    """
    The operations of LiquidStation, 
    include: open_bottle, close_bottle, add_liquid, transfer_liquid
    """
    def __init__(self, 
                 axis_gripper_op: LS_Axis_Gripper_op,  
                 syringepump_op: SyringePump_op, 
                 hotplate_op: HotPlate_op, 
                 moving_stage_op: Leadshine_Motor_op, 
                 pH_test_op: pH_Test_op, 
                 uv_vis_setup: UV_vis_setup,
                 pH_adjust_env: PHAdjustmentEnv, 
                 mapping: dict,
                 storage_mapping: dict, 
                 current_mapping: dict, 
                 info: dict, 
                 logger: logging.Logger):
        """
        initialize the LiquidStation

        Args:
            head_vial_mapping_path: the mapping path of the vial, cap and head
            axis_gripper_op: the operation of multi-axis system and two dh_grippers
            syringepump_op: the operation of syringepump and switchvalve
            hotplate_op: the operation of DLAB hotplate
            moving_stage_op: the operation of movingstage
            uv_vis_setup: the operation of uv_vis_setup
            mapping: the mapping of vial, cap, head
            storage_mapping: the storage mapping of vial, cap, head
            current_mapping: the current mapping of vial, cap, head
            info: a dict contains infomation of liquidstation
            logger: logger
        """
        # define the configuration dict 
        self.mapping = mapping
        self.storage_mapping = storage_mapping
        self.current_mapping = current_mapping
        self.info = info
        self.cap_capacity = self.info["cap_holders"]["info"][0] * self.info["cap_holders"]["info"][1]
        self.tip_capacity = self.info["pipette_tips"]["info"][0]
        # initialize the logger
        self.logger = logger
        # initialize the operations out of the devices
        self.axis_gripper_op = axis_gripper_op
        self.syringepump_op = syringepump_op
        self.hotplate_op = hotplate_op
        self.moving_stage_op = moving_stage_op
        self.pH_test_op = pH_test_op
        self.uv_vis_setup = uv_vis_setup
        self.pH_adjust_env = pH_adjust_env
        self.pH_clean = False

    def _close_bottle(self):
        """
        close the vial on the pge50_platform.
        if there is no vial on the pge50_platform, raise error.                 
        """
        # ensure the target vial is on pge50_platform
        current_reactor = check_obj_status("vial", "pge50_platform", 0, self.current_mapping)
        if not current_reactor:
            raise ValueError("the pge50_platform is empty!")
        # close the bottle
        flag = True
        for cap_idx in range(self.cap_capacity):
            target_cap = check_obj_status("cap", "cap_holders", cap_idx, self.current_mapping)
            if target_cap != False:
                self.axis_gripper_op._close_bottle(cap_idx)
                self.current_mapping["Vials"][current_reactor]["capped"] = target_cap
                self.current_mapping["Caps"][target_cap]["cap_plate"] = current_reactor
                self.current_mapping["Caps"][target_cap]["slot_index"] = 0
                flag = False
                break
        if flag:
            raise ValueError("there is no enough cap to close bottle!")    
                                            
    def _open_bottle(self):
        """
        open the vial on the pge50_platform.
        if there is no vial on the pge50_platform, raise error.
        """
        # find the current location of the reactor and dosing head 
        # close it 
        current_reactor = check_obj_status("vial", "pge50_platform", 0, self.current_mapping)
        if not current_reactor:
            raise ValueError("the pge50_platform is empty!")
        flag = True
        for cap_idx in range(self.cap_capacity):
            target_cap = check_obj_status("cap", "cap_holders", cap_idx, self.current_mapping)
            if not target_cap:
                current_cap = self.current_mapping["Vials"][current_reactor]["capped"]
                self.axis_gripper_op._open_bottle(cap_idx)
                self.current_mapping["Vials"][current_reactor]["capped"] = False
                self.current_mapping["Caps"][current_cap]["cap_plate"] = "cap_holders"
                self.current_mapping["Caps"][current_cap]["slot_index"] = cap_idx
                flag = False
                break 
        if flag:
            raise ValueError("there is no empty holder to hold cap!")

    def _add_liquid(self, 
                    reactor: str, 
                    solution: list, 
                    volume: list, 
                    z1_offset: float = 60, 
                    add_speed = 1.75,
                    if_return: bool = True, 
                    if_clean: bool = True):
        """
        add liquid to a reactor
        Args:
            reactor: the name of the reactor
            solution: array, the names of the kinds of solution
            volume: array, the volume of the liquid in mL
        """
        for v in volume:
            if v < 0:
                raise ValueError("Volume must not smaller than 0!")
            
        if sum([v == 0 for v in volume]) == len(volume):
            return 
        # find the current location of the reactor 
        vial_info = self.current_mapping["Vials"][reactor]
        current_holder = vial_info["bottle_plate"]
        # record the current feeder index
        feeder_on_rgi30 = check_obj_status("feeder", "rgi30", 0, self.current_mapping)
        if current_holder == "bottle_holders":
            feeder_index = int(self.current_mapping["Vials"][reactor]["slot_index"] // self.info["bottle_holders"]["info"][0])
            feed_name = "liquid_feed"
            if (feeder_on_rgi30) and (feeder_on_rgi30 != f"feeder_{feeder_index}"):
                self.axis_gripper_op._place_obj("liquid_feeders", int(feeder_on_rgi30[-1]))
                self.current_mapping["Feeders"][feeder_on_rgi30] = "home"
        elif current_holder == "uv_vis_holder":
            feeder_index = 0
            feed_name = "uv_vis_feed"
            if (feeder_on_rgi30) and (feeder_on_rgi30 != f"feeder_{feeder_index}"):
                self.axis_gripper_op._place_obj("liquid_feeders", int(feeder_on_rgi30[-1]))
                self.current_mapping["Feeders"][feeder_on_rgi30] = "home"
        elif current_holder == "heat_bottle_holders":
            feeder_index = self.info["liquid_feeders"]["info"][1] -1
            feed_name = "heater_feed"
            if (feeder_on_rgi30) and (feeder_on_rgi30 != f"feeder_{feeder_index}"):
                self.axis_gripper_op._place_obj("liquid_feeders", int(feeder_on_rgi30[-1]))
                self.current_mapping["Feeders"][feeder_on_rgi30] = "home"
        else:
            raise ValueError(f"the current_holder is not correct holder, current value is {current_holder}")
        # find the current location of the feeder
        feeder_info = self.current_mapping["Feeders"][f'feeder_{feeder_index}']
        
        # place the liquid_feeder on the top of the vial
        if feeder_info == "home":
            self.axis_gripper_op._get_obj("liquid_feeders", feeder_index)
            self.current_mapping["Feeders"][f'feeder_{feeder_index}'] = "rgi30"
        self.axis_gripper_op._place_obj(feed_name, vial_info["slot_index"], open_rgi30 = False, z1_offset = z1_offset)
        
        # iterate through all solutions
        for sol_idx in range(len(solution)):
            # dispense liquid into the vial
            self.syringepump_op.pipette_liquids(volume[sol_idx], 
                                                solution[sol_idx], 
                                                f'feeder_{feeder_index}',
                                                out_speed = add_speed)
            
        # place the liquid feeder back to its holder
        if if_return:
            self.axis_gripper_op._place_obj("liquid_feeders", feeder_index)
            self.current_mapping["Feeders"][f'feeder_{feeder_index}'] = "home"
            if if_clean:
                for i in range(3):
                    self.syringepump_op.dispense_liquid(3, "H2O", f"feeder_{feeder_index}", in_speed=HIGH_SPEED)
                    self.syringepump_op.dispense_liquid(5, f"feeder_{feeder_index}", "wasteout")
                # deliver the water to waste to make sure the tube is empty
                self.syringepump_op.dispense_liquid(5, "air", "wasteout")
        return True
    
    def _transfer_liquid(self, 
                        reactor_0: str, 
                        reactor_1: str, 
                        volume: float, 
                        transfer_speed: int = 5/6, 
                        z2_offset_0: float = -69.5, 
                        z2_offset_1: float = -5, 
                        mix_method: Optional[str] = None):
        """
        Transfer liquid from reactor_0 to reactor_1 through pipette.

        Args:
            reactor_0: the name of the reactor_0 whose liquid will be absorbed
            reactor_1: the name of the reactor_1 in which the liquid will be injected
            volume: the volume of liquid
            if_mix: flag to judge whether mix is needed. Defaults to False.
        """
        # define the current information of two reactors
        vial_info_0 = self.current_mapping["Vials"][reactor_0]
        vial_info_1 = self.current_mapping["Vials"][reactor_1]
        # get the target place where the injector shoulder go
        if vial_info_0["bottle_plate"] == "bottle_holders":
            inject_place_0 = "liquid_inject"
        elif vial_info_0["bottle_plate"] == "heat_bottle_holders":
            inject_place_0 = "heater_inject"
        elif vial_info_0["bottle_plate"] == "uv_vis_holder":
            inject_place_0 = "uv_vis_inject"
        elif vial_info_0["bottle_plate"] == "storage_holders":
            inject_place_0 = "storage_inject"
        else:
            raise ValueError(f"reactor_0 should in bottle_holders or heat_bottle_holders, current value is {vial_info_0['bottle_plate']}")
        # get the target place where the injector shoulder go
        if vial_info_1["bottle_plate"] == "bottle_holders":
            inject_place_1 = "liquid_inject"
        elif vial_info_1["bottle_plate"] == "heat_bottle_holders":
            inject_place_1 = "heater_inject"
        elif vial_info_1["bottle_plate"] == "uv_vis_holder":
            inject_place_1 = "uv_vis_inject"
        elif vial_info_1["bottle_plate"] == "storage_holders":
            inject_place_1 = "storage_inject"
        else:
            raise ValueError(f"reactor_1 should in bottle_holders or heat_bottle_holders, current value is {vial_info_1['bottle_plate']}")
        # find the tip which is on tip holder
        for idx in range(self.tip_capacity):
            tip_on_holder = check_obj_status("tip", None , idx = idx, mapping = self.current_mapping)
            if tip_on_holder:
                self.axis_gripper_op._get_pipette_tip(idx)
                break
        stir_status = self.hotplate_op.hotplate.quary_info("stir_status")
        absorb_speed = (5/6)

        last_mix = False
        if volume <= 0.1:
            absorb_speed = 0.1
            last_mix = True
        while volume > 0:
            if (stir_status == 0) and (inject_place_0 == "heater_inject"):
                self.hotplate_op.hotplate.turn_stir_off()
            self.axis_gripper_op._place_obj(inject_place_0, vial_info_0["slot_index"], z2_offset = z2_offset_0)
            time.sleep(1)
            if volume > self.axis_gripper_op.injector.max_tip_volume: 
                self.axis_gripper_op._absorb_liquid(self.axis_gripper_op.injector.max_tip_volume, absorb_speed)
                self.axis_gripper_op._place_obj(inject_place_1, vial_info_1["slot_index"], z2_offset = z2_offset_1)
                if stir_status == 0 and (inject_place_0 == "heater_inject"):
                    self.hotplate_op.hotplate.turn_stir_on()
                self.axis_gripper_op._inject_liquid(transfer_speed)
                volume -= self.axis_gripper_op.injector.max_tip_volume
            else: 
                self.axis_gripper_op._absorb_liquid(volume, absorb_speed)
                self.axis_gripper_op._place_obj(inject_place_1, vial_info_1["slot_index"], z2_offset = -60)
                if stir_status == 0 and (inject_place_0 == "heater_inject"):
                    self.hotplate_op.hotplate.turn_stir_on()
                self.axis_gripper_op._inject_liquid(transfer_speed)
                if last_mix:
                    self.axis_gripper_op._place_obj(inject_place_1, vial_info_1["slot_index"], z2_offset = -60)
                    self.axis_gripper_op._mix_liquid(self.axis_gripper_op.injector.max_tip_volume, 2)
                volume = 0
        if mix_method == "injector":
            self.axis_gripper_op._place_obj(inject_place_1, vial_info_1["slot_index"], z2_offset = -60)
            self.axis_gripper_op._mix_liquid(self.axis_gripper_op.injector.max_tip_volume, 2)
        elif mix_method == "magnetic":
            if vial_info_1["bottle_plate"] == "head_bottle_holders":
                self.hotplate_op.stir(10, DEFAULT_STIR_SPEED)
            elif vial_info_1["bottle_plate"] == "uv_vis_holder":
                self.pH_test_op._magnetic_stir(5, DEFAULT_STIR_SPEED)
            else: 
                raise SyntaxError("the mix_method must be used when the reactor_1 is on heater or uv_vis_holder.")
        self.axis_gripper_op._place_obj("rubbish_bin_tip", 0)
        self.axis_gripper_op._push_actuator()
        self.current_mapping["Tips"][tip_on_holder] = "rubbish_bin_tip"

    def _ensure_pH_meter_safety_(self, x_thresold: float = 50, y_thresold: float = 150):
        """
        make sure the pH meter is safe 
        """
        # get the current location of the axis gripper 
        aquire(self.axis_gripper_op.axismotion)
        position_x = self.axis_gripper_op.axismotion.read_position('x')
        position_y = self.axis_gripper_op.axismotion.read_position('y')
        release(self.axis_gripper_op.axismotion)
        # if it is at certain region, move it. 
        # FIXME 
        # to move the pH meter to a specific location 
        if position_x < x_thresold or position_y < y_thresold:
            aquire(self.axis_gripper_op.axismotion)
            self.axis_gripper_op.axismotion._move_xyz([100, 300, 0, 0])
            release(self.axis_gripper_op.axismotion)
        return True 

    def _wash_pHmeter(self):
        """
        Wash the pH meter.
        """
        current_pos = self.current_mapping["pHMeter"]["position"]
        if current_pos != "pH_storage":
            self._ensure_pH_meter_safety_()
            self.pH_test_op.move_pH_meter_to(
                spin = self.pH_test_op.spin_locations[0], 
                z = self.pH_test_op.storage_z_location
            )
            
            self.current_mapping["pHMeter"]["position"] = "pH_storage"
            self.current_mapping["pHMeter"]["slot_index"] = 0
        self.pH_test_op.clean_cell()

    def _store_pHmeter(self):
        """
        Store the pH meter in KCl solution.
        """
        current_pos = self.current_mapping["pHMeter"]["position"]
        if current_pos != "pH_storage":
            self._ensure_pH_meter_safety_()
            self.pH_test_op.move_pH_meter_to(
                spin = self.pH_test_op.spin_locations[0], 
                z = self.pH_test_op.storage_z_location
            )
            self.current_mapping["pHMeter"]["position"] = "pH_storage"
            self.current_mapping["pHMeter"]["slot_index"] = 0
        self.pH_test_op.refresh_KCl()

    def _calibrate_pHmeter(self, buffer_info: dict =  {4.00: 0, 6.86: 1, 9.18: 2}):
        """
        Calibrate pH by using two standard solution.

        Args:
            buffer_info
        """
        self._ensure_pH_meter_safety_()
        # empty the reference 
        self.pH_test_op.pHmeter.reset_ref()

        # read the value of all the reference samples
        count = 1
        for pH_temp in buffer_info.keys():
            # wash the pH meter and put the pH meter into the buffer_0
            self._wash_pHmeter()
            self.pH_test_op.move_pH_meter_to(
                spin = self.pH_test_op.spin_locations[count], 
                z = self.pH_test_op.z_location
            )
            self.current_mapping["pHMeter"]["position"] = f"pH_buffer"
            self.current_mapping["pHMeter"]["slot_index"] = buffer_info[pH_temp]
            time.sleep(10)
            self.pH_test_op.pHmeter.record_ref(pH_temp)
            count = count + 1 
        self.pH_test_op.pHmeter.calibrate_meter()
        self._wash_pHmeter()
        return True


    def _read_pH(self):
        """
        Read the pH while pH meter is in the solution.

        Returns:
            the pH value
        """
        pH = self.pH_test_op.read_pH()
        print(pH)
        return pH
    
    def _adjust_pH_to(
            self, 
            target_pH: float, 
            tolerance: float, 
            step_volume: float = 0.05, 
            if_calibrate: bool = True, 
            try_max = 40,
            allowed_pumps = ["pump_pH_acid", "pump_pH_base"], 
            stir_speed: int = 600, 
            store: bool = True, 
            stir_time: int = 60
            ) -> float:
        """
        Adjust the pH solution to a selected pH range.

        Args:
            target_pH: the target pH. 
            tolerance: the tolerance of pH. unit: None.
            step_volume: the volume of acid or base added while adjusting pH. Defaults to 0.1 mL.
            if_calibrate: if calibrate the pH meter before the operation 
            try_max: maximum amount of tries F
            specific_reagents: use the specific reagents to adjust the pH. If None, both acid and base pump will be used. 
        Raises:
            ValueError: while target pH is out of 0~14.

        Returns:
            adjusted pH value.
        """
        # judge which buffer should be used to calibrate pH meter
        self._ensure_pH_meter_safety_()
        if (if_calibrate): 
            self._calibrate_pHmeter()
            
        if (target_pH <= 0) or (target_pH >= 14): 
            raise ValueError(f"the target pH should be in the range (0, 14), current value is {target_pH}")
        
            
        # get the range of target pH
        upper = target_pH + tolerance
        lower = target_pH - tolerance
    
        # move the pHmeter to the uv_vis_holder
        current_pos = self.current_mapping["pHMeter"]["position"]
        if current_pos != "pH_adjust":
            self._wash_pHmeter()
            self.pH_test_op.move_pH_meter_to(
                spin = self.pH_test_op.spin_locations[-1], 
                z = self.pH_test_op.z_location
            )
            self.current_mapping["pHMeter"]["position"] = "pH_adjust"
            self.current_mapping["pHMeter"]["slot_index"] = 0
        
        # adjust pH by adding acid or base if not specific_reagents are required
        pH_total = {}
        acid_volume = {0: 0}
        base_volume = {0: 0}
        self.pH_test_op._magnetic_stir(stir_time, stir_speed)
        current_pH = self._read_pH()
        pH_total[0] = current_pH
        acid = 0
        base = 0
        drop_num = 0

        if len(allowed_pumps) == 2:
            # adjust the pH according to the allowed reagents
            for i in range(try_max):
                last_pH = current_pH
                if current_pH > upper:
                    self.pH_test_op.pump_acid.dispense_liquid(step_volume)
                    drop_num += 1
                    self.pH_test_op._magnetic_stir(stir_time, stir_speed)
                    time.sleep(2)
                    current_pH = self._read_pH()
                    pH_total[drop_num] = current_pH
                    acid += step_volume
                    acid_volume[drop_num] = acid

                elif current_pH < lower:
                    self.pH_test_op.pump_base.dispense_liquid(step_volume)
                    drop_num += 1
                    self.pH_test_op._magnetic_stir(stir_time, stir_speed)
                    time.sleep(2)
                    current_pH = self._read_pH()
                    pH_total[drop_num] = current_pH
                    base += step_volume
                    base_volume[drop_num] = base
                else:
                    break
                # if the range(last_pH) is bigger than the target_pH with tolerance, smallize the step_volume
                pH_list = [current_pH, last_pH, target_pH]
                pH_list.sort()
                if pH_list.index(target_pH) == 1:
                    step_volume *= 0.8
        elif allowed_pumps[0] == "pump_pH_base":
            # adjust the pH according to the allowed reagents
            for i in range(try_max):
                if current_pH < lower:
                    self.pH_test_op.pump_base.dispense_liquid(step_volume)
                    drop_num += 1
                    self.pH_test_op._magnetic_stir(stir_time, stir_speed)
                    time.sleep(2)
                    current_pH = self._read_pH()
                    pH_total[drop_num] = current_pH
                    base += step_volume
                    base_volume[drop_num] = base
                else:
                    break

        elif allowed_pumps[0] == "pump_pH_acid":
            # adjust the pH according to the allowed reagents
            for i in range(try_max):
                if current_pH > upper:
                    self.pH_test_op.pump_acid.dispense_liquid(step_volume)
                    drop_num += 1
                    self.pH_test_op._magnetic_stir(stir_time, stir_speed)
                    current_pH = self._read_pH()
                    pH_total[drop_num] = current_pH
                    acid += step_volume
                    acid_volume[drop_num] = acid
                else:
                    break

        # store the pHmeter after adjusting pH
        self._wash_pHmeter()
        if store:
            self._store_pHmeter()
        self.logger.info(f'the current pH of solution is {current_pH}')
        total_data = {
            "pH": pH_total, 
            "acid": acid_volume, 
            "base": base_volume
        }

        return total_data
    
    def _adjust_pH_to_complex_case(
            self, 
            target_pH: float, 
            tolerance: float, 
            if_calibrate: bool = True, 
            try_max = 40,
            allowed_pumps = ["pump_pH_acid", "pump_pH_base"], 
            stir_speed: int = 300, 
            store: bool = True
            ) -> float:
        
        """
        Adjust the pH solution to a selected pH range.

        Args:
            target_pH: the target pH. 
            tolerance: the tolerance of pH. unit: %.
            step_volume: the volume of acid or base added while adjusting pH. Defaults to 0.1 mL.
            if_calibrate: if calibrate the pH meter before the operation 
            try_max: maximum amount of tries 
            specific_reagents: use the specific reagents to adjust the pH. If None, both acid and base pump will be used. 
        Raises:
            ValueError: while target pH is out of 0~14.

        Returns:
            adjusted pH value.
        """
        # judge which buffer should be used to calibrate pH meter
        self._ensure_pH_meter_safety_()
        if (if_calibrate): 
            self._calibrate_pHmeter()
            
        if (target_pH <= 0) or (target_pH >= 14): 
            raise ValueError(f"the target pH should be in the range (0, 14), current value is {target_pH}")
        
            
        # get the range of target pH
        upper = target_pH + tolerance
        lower = target_pH - tolerance
    
        # move the pHmeter to the uv_vis_holder
        current_pos = self.current_mapping["pHMeter"]["position"]
        if current_pos != "pH_adjust":
            self._wash_pHmeter()
            self.pH_test_op.move_pH_meter_to(
                spin = self.pH_test_op.spin_locations[-1], 
                z = self.pH_test_op.z_location
            )
            self.current_mapping["pHMeter"]["position"] = "pH_adjust"
            self.current_mapping["pHMeter"]["slot_index"] = 0
        
        # adjust pH by adding acid or base if not specific_reagents are required
        pH_total = {}
        acid_volume = {0: 0}
        base_volume = {0: 0}
        self.pH_test_op._magnetic_stir(30, stir_speed)
        current_pH = self._read_pH()
        pH_total[0] = current_pH
        acid = 0
        base = 0
        drop_num = 0

        step_volume = 11.02*((10**(-current_pH)) - (10**(-target_pH)))/0.1*0.5

        if len(allowed_pumps) == 2:
            # adjust the pH according to the allowed reagents
            for i in range(try_max):
                last_pH = current_pH
                if current_pH > upper:
                    self.pH_test_op.pump_acid.dispense_liquid(step_volume)
                    drop_num += 1
                    self.pH_test_op._magnetic_stir(30, stir_speed)
                    time.sleep(2)
                    current_pH = self._read_pH()
                    pH_total[drop_num] = current_pH
                    acid += step_volume
                    acid_volume[drop_num] = acid

                elif current_pH < lower:
                    self.pH_test_op.pump_base.dispense_liquid(step_volume)
                    drop_num += 1
                    self.pH_test_op._magnetic_stir(30, stir_speed)
                    time.sleep(2)
                    current_pH = self._read_pH()
                    pH_total[drop_num] = current_pH
                    base += step_volume
                    base_volume[drop_num] = base
                else:
                    break
                # if the range(last_pH) is bigger than the target_pH with tolerance, smallize the step_volume
                pH_list = [current_pH, last_pH, target_pH]
                pH_list.sort()
                if pH_list.index(target_pH) == 1:
                    step_volume *= 0.8
        elif allowed_pumps[0] == "pump_pH_base":
            # adjust the pH according to the allowed reagents
            for i in range(try_max):
                if current_pH < lower:
                    self.pH_test_op.pump_base.dispense_liquid(step_volume)
                    drop_num += 1
                    self.pH_test_op._magnetic_stir(30, stir_speed)
                    time.sleep(2)
                    current_pH = self._read_pH()
                    pH_total[drop_num] = current_pH
                    base += step_volume
                    base_volume[drop_num] = base
                else:
                    break

        elif allowed_pumps[0] == "pump_pH_acid":
            # adjust the pH according to the allowed reagents
            for i in range(try_max):
                if current_pH > upper:
                    self.pH_test_op.pump_acid.dispense_liquid(step_volume)
                    drop_num += 1
                    self.pH_test_op._magnetic_stir(30, stir_speed)
                    current_pH = self._read_pH()
                    pH_total[drop_num] = current_pH
                    acid += step_volume
                    acid_volume[drop_num] = acid
                else:
                    break

        # store the pHmeter after adjusting pH
        self._wash_pHmeter()
        if store:
            self._store_pHmeter()
        self.logger.info(f'the current pH of solution is {current_pH}')
        total_data = {
            "pH": pH_total, 
            "acid": acid_volume, 
            "base": base_volume
        }

        return total_data

    def _adjust_pH_to_fast_ver(
            self, 
            target_pH: float, 
            tolerance: float, 
            if_calibrate: bool = True, 
            try_max = 40,
            allowed_pumps = ["pump_pH_acid", "pump_pH_base"], 
            stir_speed: int = 300, 
            store: bool = True
            ) -> float:
        """
        Adjust the pH solution to a selected pH range.

        Args:
            target_pH: the target pH. 
            tolerance: the tolerance of pH. unit: %.
            step_volume: the volume of acid or base added while adjusting pH. Defaults to 0.1 mL.
            if_calibrate: if calibrate the pH meter before the operation 
            try_max: maximum amount of tries 
            specific_reagents: use the specific reagents to adjust the pH. If None, both acid and base pump will be used. 
        Raises:
            ValueError: while target pH is out of 0~14.

        Returns:
            adjusted pH value.
        """
        # judge which buffer should be used to calibrate pH meter
        

        self._ensure_pH_meter_safety_()
        if (if_calibrate): 
            self._calibrate_pHmeter()
            
        if (target_pH <= 0) or (target_pH >= 14): 
            raise ValueError(f"the target pH should be in the range (0, 14), current value is {target_pH}")
        
            
        # get the range of target pH
        upper = target_pH + tolerance
        lower = target_pH - tolerance
    
        # move the pHmeter to the uv_vis_holder
        current_pos = self.current_mapping["pHMeter"]["position"]
        if current_pos != "pH_adjust":
            self._wash_pHmeter()
            self.pH_test_op.move_pH_meter_to(
                spin = self.pH_test_op.spin_locations[-1], 
                z = self.pH_test_op.z_location
            )
            self.current_mapping["pHMeter"]["position"] = "pH_adjust"
            self.current_mapping["pHMeter"]["slot_index"] = 0
        
        # adjust pH by adding acid or base if not specific_reagents are required
        pH_total = {}
        acid_volume = {0: 0}
        base_volume = {0: 0}
        self.pH_test_op._magnetic_stir(30, stir_speed)
        current_pH = self._read_pH()
        self.pH_adjust_env._initialize_env(current_pH, target_pH, try_max)
        action, done = self.pH_adjust_env.select_best_action()
        pH_total[0] = current_pH
        acid = 0
        base = 0
        drop_num = 0

        while done == False:
            if action[0] == list(reagents.keys())[0]:
                self.pH_test_op.pump_acid.dispense_liquid(action[1])
                drop_num += 1
                acid += action[1]
                self.pH_test_op._magnetic_stir(30, 600)
                current_pH = self._read_pH()
                pH_total[drop_num] = current_pH
                action, done = self.pH_adjust_env.suggest_next_action(action, current_pH)
            else:
                self.pH_test_op.pump_base.dispense_liquid(action[1])
                drop_num += 1
                base += action[1]
                self.pH_test_op._magnetic_stir(30, 600)
                current_pH = self._read_pH()
                pH_total[drop_num] = current_pH
                action, done = self.pH_adjust_env.suggest_next_action(action, current_pH)
        # store the pHmeter after adjusting pH
        self._wash_pHmeter()
        if store:
            self._store_pHmeter()
        self.logger.info(f'the current pH of solution is {current_pH}')
        total_data = {
            "pH": pH_total, 
            "acid": acid_volume, 
            "base": base_volume
        }

        return total_data
    
    # def _adjust_pH_to_2base_ver(
    #         self, 
    #         target_pH: float, 
    #         tolerance: float, 
    #         step_volume: float = 0.1, 
    #         if_calibrate: bool = True, 
    #         try_max = 40,
    #         stir_speed: int = 300, 
    #         store: bool = True
    #         ) -> float:
    #     """
    #     Adjust the pH solution to a selected pH range.

    #     Args:
    #         target_pH: the target pH. 
    #         tolerance: the tolerance of pH.
    #         step_volume: the volume of acid or base added while adjusting pH. Defaults to 0.1 mL.
    #         if_calibrate: if calibrate the pH meter before the operation 
    #         try_max: maximum amount of tries 
    #         specific_reagents: use the specific reagents to adjust the pH. If None, both acid and base pump will be used. 
    #     Raises:
    #         ValueError: while target pH is out of 0~14.

    #     Returns:
    #         adjusted pH value.
    #     """
    #     # judge which buffer should be used to calibrate pH meter
    #     self._ensure_pH_meter_safety_()
    #     if (if_calibrate): 
    #         self._calibrate_pHmeter()
            
    #     if (target_pH <= 0) or (target_pH >= 14): 
    #         raise ValueError(f"the target pH should be in the range (0, 14), current value is {target_pH}")
        
            
    #     # get the range of target pH
    #     lower_0 = target_pH - 5 * tolerance
    #     lower_1 = target_pH - tolerance
    
    #     # move the pHmeter to the uv_vis_holder
    #     current_pos = self.current_mapping["pHMeter"]["position"]
    #     if current_pos != "pH_adjust":
    #         self._wash_pHmeter()
    #         self.pH_test_op.move_pH_meter_to(
    #             spin = self.pH_test_op.spin_locations[-1], 
    #             z = self.pH_test_op.z_location
    #         )
    #         self.current_mapping["pHMeter"]["position"] = "pH_adjust"
    #         self.current_mapping["pHMeter"]["slot_index"] = 0
        
    #     # adjust pH by adding acid or base if not specific_reagents are required
    #     pH_total = []
    #     base_0_volume = [0]
    #     base_1_volume = [0]
    #     time.sleep(10)
    #     current_pH = self._read_pH()
    #     pH_total.append(current_pH)

    #     if current_pH >= lower_1:
    #         self._wash_pHmeter()
    #         if store:
    #             self._store_pHmeter()

    #         total_data = {
    #             "pH": pH_total, 
    #             "base_0": base_0_volume, 
    #             "base_1": base_1_volume
    #         }
    #         return total_data
        
    #     base_0 = 0
    #     base_1 = 0
    #     # adjust the pH according to the allowed reagents
    #     self.pH_test_op.pump_base.dispense_liquid(step_volume)
    #     self.pH_test_op.move_pH_meter_to(self.pH_test_op.spin_locations[-1], 0)        
    #     self.pH_test_op._magnetic_stir(10, stir_speed)
    #     self.pH_test_op.move_pH_meter_to(self.pH_test_op.spin_locations[-1], self.pH_test_op.z_location)
    #     last_pH = current_pH

    #     current_pH = self._read_pH()
    #     pH_total.append(current_pH)
    #     base_1 += step_volume
    #     base_1_volume.append(base_1)

    #     add_dilute = False
    #     if current_pH - last_pH >= 0.2:
    #         add_dilute = True

    #     for i in range(try_max):

    #         last_pH = current_pH
    #         # if the pH value is below the thresold
    #         if (current_pH < lower_0):
    #             # we use concentrated base 
    #             if (add_dilute == False):
    #                 self.pH_test_op.pump_acid.dispense_liquid(step_volume)
    #                 self.pH_test_op._magnetic_stir(10, stir_speed)
    #                 current_pH = self._read_pH()

    #                 pH_total.append(current_pH)
    #                 base_0 += step_volume
    #                 base_0_volume.append(base_0)
    #             # use diluted base 
    #             else:
    #                 self.pH_test_op.pump_base.dispense_liquid(step_volume)
    #                 self.pH_test_op._magnetic_stir(10, stir_speed)
    #                 current_pH = self._read_pH()
    #                 pH_total.append(current_pH)
    #                 base_1 += step_volume
    #                 base_1_volume.append(base_1)

    #         # use diluted base
    #         elif (lower_0 < current_pH < lower_1):
    #             self.pH_test_op.pump_base.dispense_liquid(step_volume)
    #             self.pH_test_op._magnetic_stir(10, stir_speed)
    #             current_pH = self._read_pH()
    #             pH_total.append(current_pH)
    #             base_1 += step_volume
    #             base_1_volume.append(base_1)
    #         else:
    #             break
            
    #     # store the pHmeter after adjusting pH
    #     self._wash_pHmeter()
    #     if store:
    #         self._store_pHmeter()
    #     self.logger.info(f'the current pH of solution is {current_pH}')
    #     total_data = {
    #         "pH": pH_total, 
    #         "base_0": base_0_volume, 
    #         "base_1": base_1_volume
    #     }
    #     return total_data
    
    # def _adjust_pH_to_spec_ver(
    #     self, 
    #     target_pH: float, 
    #     tolerance: int, 
    #     step_volume: float = 0.05, 
    #     if_calibrate: bool = True, 
    #     try_max = 40,
    #     specific_reagents = None, 
    #     stir_speed: int = 300
    #     ) -> float:
    #     """
    #     Adjust the pH solution to a selected pH range.

    #     Args:
    #         target_pH: the target pH. 
    #         tolerance: the tolerance of pH. unit: %.
    #         step_volume: the volume of acid or base added while adjusting pH. Defaults to 0.1 mL.
    #         if_calibrate: if calibrate the pH meter before the operation 
    #         try_max: maximum amount of tries 
    #         specific_reagents: use the specific reagents to adjust the pH. If None, both acid and base pump will be used. 
    #     Raises:
    #         ValueError: while target pH is out of 0 ~ 14.

    #     Returns:
    #         adjusted pH value.
    #     """
    #     # judge which buffer should be used to calibrate pH meter
    #     self._ensure_pH_meter_safety_()
    #     if (if_calibrate): 
    #         self._calibrate_pHmeter()
            
    #     if (target_pH <= 0) or (target_pH >= 14): 
    #         raise ValueError(f"the target pH should be in the range (0, 14), current value is {target_pH}")
        
    #     # if not specific reagents we should use, we can continue as normal.
    #     if specific_reagents == None:
    #         allowed_reagents =  [
    #                             self.pH_test_op.pump_acid_name, 
    #                             self.pH_test_op.pump_base_name
    #                             ]
            
    #     # make sure all the desired reagents are in pump_acid or pump_base
    #     else:
    #         if len(specific_reagents)>2:
    #             raise ValueError(f"maximum two reagents can be used to tune the pH! current specific reagent: {specific_reagents}")
    #         # add the allowed reagents to the list
    #         allowed_reagents = []
    #         for reagent in specific_reagents:
    #             if reagent not in [self.pH_test_op.pump_acid_name, self.pH_test_op.pump_base_name]:
    #                 raise ValueError(f"reagent {reagent} is not supported in the current setup!")
    #             else:
    #                 allowed_reagents.append(reagent)
            
    #     # get the range of target pH
    #     upper = target_pH * (1 + 0.01 * tolerance)
    #     lower = target_pH * (1 - 0.01 * tolerance)

    #     # move the pHmeter to the uv_vis_holder
    #     current_pos = self.current_mapping["pHMeter"]["position"]
    #     if current_pos != "pH_adjust":
    #         self._wash_pHmeter()
    #         self.pH_test_op.move_pH_meter_to(
    #             spin = self.pH_test_op.spin_locations[-1], 
    #             z = self.pH_test_op.z_location
    #         )
    #         self.current_mapping["pHMeter"]["position"] = "pH_adjust"
    #         self.current_mapping["pHMeter"]["slot_index"] = 0
        
    #     # adjust pH by adding acid or base if not specific_reagents are required
    #     pH_total = []
    #     acid_volume = []
    #     base_volume = []
    #     spec_total = []
    #     current_pH = self._read_pH()
    #     pH_total.append(current_pH)
    #     acid = 0
    #     base = 0
    #     if len(allowed_reagents) == 2:
    #         # adjust the pH according to the allowed reagents
    #         for i in range(try_max):
    #             if current_pH > upper:
    #                 self.pH_test_op.pump_acid.dispense_liquid(step_volume)
    #                 self.pH_test_op._magnetic_stir(10, stir_speed)
    #                 wavelength, intensity = self.uv_vis_setup.obtain_raw_spectrum()
    #                 spec_total.append([wavelength, intensity])
    #                 current_pH = self._read_pH()
    #                 pH_total.append(current_pH)
    #                 acid_volume.append(acid + step_volume)

    #             elif current_pH < lower:
    #                 self.pH_test_op.pump_base.dispense_liquid(step_volume)
    #                 self.pH_test_op._magnetic_stir(10, stir_speed)
    #                 wavelength, intensity = self.uv_vis_setup.obtain_raw_spectrum()
    #                 spec_total.append([wavelength, intensity])
    #                 current_pH = self._read_pH()
    #                 pH_total.append(current_pH)
    #                 base_volume.append(base + step_volume)
    #             else:
    #                 break
    #     elif allowed_reagents[0] == self.pH_test_op.pump_base_name:
    #         # adjust the pH according to the allowed reagents
    #         for i in range(try_max):
    #             if current_pH < lower:
    #                 self.pH_test_op.pump_base.dispense_liquid(step_volume)
    #                 self.pH_test_op._magnetic_stir(10, stir_speed)
    #                 wavelength, intensity = self.uv_vis_setup.obtain_raw_spectrum()
    #                 spec_total.append([wavelength, intensity])
    #                 current_pH = self._read_pH()
    #                 pH_total.append(current_pH)
    #             else:
    #                 break
    #     elif allowed_reagents[0] == self.pH_test_op.pump_acid_name:
    #         # adjust the pH according to the allowed reagents
    #         for i in range(try_max):
    #             if current_pH > upper:
    #                 self.pH_test_op.pump_acid.dispense_liquid(step_volume)
    #                 self.pH_test_op._magnetic_stir(10, stir_speed)
    #                 wavelength, intensity = self.uv_vis_setup.obtain_raw_spectrum()
    #                 spec_total.append([wavelength, intensity])
    #                 current_pH = self._read_pH()
    #                 pH_total.append(current_pH)
    #             else:
    #                 break

    #     # store the pHmeter after adjusting pH
    #     self._wash_pHmeter()
    #     self._store_pHmeter()
    #     self.logger.info(f'the current pH of solution is {current_pH}')
    #     total_data = {
    #         "pH": pH_total, 
    #         "spec": spec_total, 
    #         "acid": acid_volume, 
    #         "base": base_volume, 
    #     }
    #     return total_data

    def _wash_feeder(self, feeder_name: str, solvents: list):
        # remove the solution to waste 
        self.syringepump_op.dispense_liquid(1, feeder_name, "wasteout")
        # clean the tubes after the transfer operation 
        for i in range(3):
            for solvent in solvents:
                self.syringepump_op.dispense_liquid(4, solvent, feeder_name)
                self.syringepump_op.dispense_liquid(5, feeder_name, "wasteout")

                
    # def _wash_bottle(self, reactor: str, solvents: list, if_return: bool = True):
    #     """
    #     Wash the chosen bottle by chosen solvents

    #     Args:
    #         reactor: the name of the reactor
    #         solvents: 
    #     """
    #     vial_info = self.current_mapping["Vials"][reactor]
    #     current_holder = self.current_mapping["Vials"][reactor]["bottle_plate"]
    #     if current_holder == "bottle_holders":
    #         feeder_index = int(self.current_mapping["Vials"][reactor]["slot_index"] // self.info["bottle_holders"]["info"][0])
    #         feed_name = "liquid_feed"
    #         feeder_on_rgi30 = check_obj_status("feeder", "rgi30", 0, self.current_mapping)
    #         if feeder_on_rgi30 and feeder_on_rgi30 != f"feeder_{feeder_index}":
    #             self.axis_gripper_op._place_obj("liquid_feeders", int(feeder_on_rgi30[7]))
    #             self.current_mapping["Feeders"][feeder_on_rgi30] = "home"
    #     elif current_holder == "heat_bottle_holders":
    #         feeder_index = self.info["liquid_feeders"]["info"][1] -1
    #         feed_name = "heater_feed"
    #     elif current_holder == "uv_vis_holder":
    #         feeder_index = self.info["liquid_feeders"]["info"][1] -1
    #         feed_name = "uv_vis_feed"
    #     else:
    #         raise ValueError(f"the current_holder should be bottle_holders/heat_bottle_holders, current value is {current_holder}")
    #     feeder_info = self.current_mapping["Feeders"][f'feeder_{feeder_index}']
    #     # place the liquid_feeder on the top of the vial
    #     if feeder_info == "home":
    #         self.axis_gripper_op._get_obj("liquid_feeders", feeder_index)
    #         self.current_mapping["Feeders"][f'feeder_{feeder_index}'] = "rgi30"
    #     self.axis_gripper_op._place_obj(feed_name, vial_info["slot_index"], open_rgi30 = False, z1_offset = 0)
    #     for i in range(3):
    #         self.syringepump_op.dispense_liquid(self.syringepump_op.syringe_pump.volume, 
    #                                             f"feeder_{feeder_index}", 
    #                                             "wasteout")
    #     # use solvent to wash the vial
    #     for i in range(3):
    #         for solvent in solvents:
    #             self.syringepump_op.dispense_liquid(self.syringepump_op.syringe_pump.volume - 1, 
    #                                                 solvent, 
    #                                                 f'feeder_{feeder_index}', 
    #                                                 in_speed = MID_SPEED)
    #             self.syringepump_op.dispense_liquid(self.syringepump_op.syringe_pump.volume, 
    #                                                 f"feeder_{feeder_index}", 
    #                                                 "wasteout")
    #     # make sure the vial is empty
    #     for i in range(2):
    #         self.syringepump_op.dispense_liquid(self.syringepump_op.syringe_pump.volume, 
    #                                             f"feeder_{feeder_index}", 
    #                                             "wasteout")
    #     # put feeder back to home if needed
    #     if if_return:
    #         self.axis_gripper_op._place_obj("liquid_feeders", feeder_index)
    #         self.current_mapping["Feeders"][f'feeder_{feeder_index}'] = "home"

    # def trasnfer_through_head(self,
    #                           reactor_0: str, 
    #                           reactor_1: str, 
    #                           volume: float, 
    #                           tube_volume: float = 1.0, 
    #                           z1_offset_0: float = 0,
    #                           z1_offset_1: float = 36, 
    #                           if_preflush: bool = True, 
    #                           if_mix: bool = False, 
    #                           if_wash: bool = True,
    #                           if_return: bool = True, 
    #                           wash_solvent: list = ["H2O"]):
    #     """
    #     Transfer liquid from reactor_0 to reactor_1 through dispensing head.

    #     Args:
    #         reactor_0: the name of the reactor_0 whose liquid will be absorbed
    #         reactor_1: the name of the reactor_1 in which the liquid will be injected
    #         volume: the volume of liquid
    #         tube_volume: the volume of PTFE tube. Defaults to 0.8.
    #         z1_offset_0: axis_z1 offset upon reactor_0. Defaults to 0.
    #         z1_offset_1: axis_z1 offset upon reactor_1. Defaults to 36.
    #         if_preflush: flag to judge whether preflush is needed. Defaults to True.
    #         if_mix: flag to judge whether mix is needed. Defaults to False.
    #         if_wash: flag to judge whether wash is needed. Defaults to True.
    #         if_return: flag to judge whether return is needed. Defaults to True.

    #     Returns:
    #         _description_
    #     """
    #     current_holder = self.current_mapping["Vials"][reactor_0]["bottle_plate"]
    #     # record the current feeder index
    #     feeder_on_rgi30 = check_obj_status("feeder", "rgi30", 0, self.current_mapping)
    #     if current_holder == "bottle_holders":
    #         # check if the two bottles are in the same column
    #         column_index1 = self.current_mapping["Vials"][reactor_0]["slot_index"] // self.info["bottle_holders"]["info"][0]
    #         column_index2 = self.current_mapping["Vials"][reactor_1]["slot_index"] // self.info["bottle_holders"]["info"][0]
    #         if column_index1 != column_index2:
    #             raise ValueError("the two bottles are not in the same column!")
    #         feeder_index = column_index1
    #         feed_name = "liquid_feed"
    #         if (feeder_on_rgi30) and (feeder_on_rgi30 != f"feeder_{feeder_index}"):
    #             self.axis_gripper_op._place_obj("liquid_feeders", int(feeder_on_rgi30[-1]))
    #             self.current_mapping["Feeders"][feeder_on_rgi30] = "home"
    #     elif current_holder == "heat_bottle_holders":
    #         feeder_index = self.info["liquid_feeders"]["info"][1] -1
    #         feed_name = "heater_feed"
    #         if (feeder_on_rgi30) and (feeder_on_rgi30 != f"feeder_{feeder_index}"):
    #             self.axis_gripper_op._place_obj("liquid_feeders", int(feeder_on_rgi30[-1]))
    #             self.current_mapping["Feeders"][feeder_on_rgi30] = "home"
    #     else:
    #         raise ValueError(f"the current_holder should be bottle_holders/heat_bottle_holders, current value is {current_holder}")
    #     feeder_info = self.current_mapping["Feeders"][f'feeder_{feeder_index}']
    #     # piptte liquid from reactor_0 to reactor_1
    #     if feeder_info == "home":
    #         self.axis_gripper_op._get_obj("liquid_feeders", feeder_index)
    #         self.current_mapping["Feeders"][f'feeder_{feeder_index}'] = "rgi30"
    #     # make sure the pipe of feeder is empty
    #     self.axis_gripper_op._place_obj(feed_name, 
    #                                     self.current_mapping["Vials"][reactor_0]["slot_index"], 
    #                                     open_rgi30 = False, 
    #                                     z1_offset = 70)
    #     self.syringepump_op.dispense_liquid(tube_volume, f"feeder_{feeder_index}", "wasteout")
    #     self.axis_gripper_op._place_obj(feed_name, 
    #                                     self.current_mapping["Vials"][reactor_0]["slot_index"], 
    #                                     open_rgi30 = False, 
    #                                     z1_offset = z1_offset_0)
    #     if if_preflush:
    #         self.syringepump_op.absorb_liquid(tube_volume,  f'feeder_{feeder_index}')
    #         self.syringepump_op.inject_liquid("wasteout")
    #     # take in the solution from reactor_0 and dispense it to the reactor 1
    #     while volume > 0:
    #         self.axis_gripper_op._place_obj(feed_name, 
    #                                         self.current_mapping["Vials"][reactor_0]["slot_index"], 
    #                                         open_rgi30 = False, 
    #                                         z1_offset = z1_offset_0)
    #         if volume > self.syringepump_op.syringe_pump.volume:
    #             self.syringepump_op.absorb_liquid(self.syringepump_op.syringe_pump.volume, f'feeder_{feeder_index}')
    #             self.axis_gripper_op._place_obj(feed_name, 
    #                                             self.current_mapping["Vials"][reactor_1]["slot_index"], 
    #                                             open_rgi30 = False, 
    #                                             z1_offset = z1_offset_1)
    #             self.syringepump_op.inject_liquid(f'feeder_{feeder_index}')
    #             # self.syringepump_op.dispense_liquid(tube_volume, "air_1", f'feeder_{feeder_index}')
    #             volume -= self.syringepump_op.syringe_pump.volume
    #         else: 
    #             self.syringepump_op.absorb_liquid(volume, f'feeder_{feeder_index}')
    #             self.axis_gripper_op._place_obj(feed_name, 
    #                                             self.current_mapping["Vials"][reactor_1]["slot_index"], 
    #                                             open_rgi30 = False, 
    #                                             z1_offset = z1_offset_1)
    #             self.syringepump_op.inject_liquid(f'feeder_{feeder_index}')
    #             # self.syringepump_op.dispense_liquid(tube_volume, "air_1", f'feeder_{feeder_index}')
    #             volume = 0
    #     # ensure the mixing of the solution if needed
    #     if if_mix:
    #         self.syringepump_op.dispense_liquid(2, f'feeder_{feeder_index}', f'feeder_{feeder_index}')
    #     # move the feeder back to the storage location 
    #     if if_return:
    #         self.axis_gripper_op._place_obj("liquid_feeders", feeder_index)
    #         self.current_mapping["Feeders"][f'feeder_{feeder_index}'] = "home"
    #     if if_wash:
    #         self._wash_feeder(f"feeder_{feeder_index}", wash_solvent)

    #     return f'feeder_{feeder_index}'


    # def transfer_liquid(self,
    #                     switch: str, 
    #                     reactor_0: str, 
    #                     reactor_1: str, 
    #                     volume: float, 
    #                     tube_volume: float = 1.0, 
    #                     z1_offset_0: float = 0,
    #                     z1_offset_1: float = 36, 
    #                     z2_offset_0: float = 10, 
    #                     z2_offset_1: float = 38, 
    #                     if_preflush: bool = True, 
    #                     if_mix: bool = False, 
    #                     if_wash: bool = True,
    #                     if_return: bool = True, 
    #                     wash_solvent: list = ["H2O"]):
    #     """
    #     Transfer liquid from reactor_0 to reactor_1.

    #     Args:
    #         switch: the method of transfering liquid
    #         reactor_0: the name of the reactor_0 whose liquid will be absorbed
    #         reactor_1: the name of the reactor_1 in which the liquid will be injected
    #         volume: the volume of liquid
    #         tube_volume: the volume of PTFE tube. Defaults to 0.8.
    #         z1_offset_0: axis_z1 offset upon reactor_0. Defaults to 0.
    #         z1_offset_1: axis_z1 offset upon reactor_1. Defaults to 36.
    #         if_preflush: flag to judge whether preflush is needed. Defaults to True.
    #         if_mix: flag to judge whether mix is needed. Defaults to False.
    #         if_wash: flag to judge whether wash is needed. Defaults to True.
    #         if_return: flag to judge whether return is needed. Defaults to True.

    #     """
    #     if volume == 0:
    #         return True
    #     elif volume < 0: 
    #         raise ValueError(f"Volume must not be smaller than 0! Current value is {volume}")
    #     if switch == "dispensing_head":
    #         self.trasnfer_through_head(reactor_0 = reactor_0, 
    #                                               reactor_1 = reactor_1, 
    #                                               volume = volume, 
    #                                               tube_volume = tube_volume, 
    #                                               z1_offset_0 = z1_offset_0, 
    #                                               z1_offset_1 = z1_offset_1, 
    #                                               if_preflush = if_preflush, 
    #                                               if_mix = if_mix, 
    #                                               if_wash = if_wash, 
    #                                               if_return = if_return, 
    #                                               wash_solvent = wash_solvent)
    #     elif switch == "pipette":
    #         self.transfer_through_injector(reactor_0 = reactor_0, 
    #                                       reactor_1 = reactor_1,
    #                                       volume = volume,
    #                                       z2_offset_0 = z2_offset_0, 
    #                                       z2_offset_1 = z2_offset_1,  
    #                                       if_mix = if_mix)
    #     else: 
    #         raise ValueError(f"switch should be 'dispensing_head' or 'pipette', current value is {switch}.")