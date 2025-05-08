import time 
import logging
import threading
from ..utility import *
from typing import Optional, Union
from solplatform.manager.operations import FS_Axis_Gripper_op, Leadshine_Motor_op

class FiltrationStation:
    """
    the operations on filtration station.
    """
    def __init__(self, 
                 axis_gripper_op: FS_Axis_Gripper_op, 
                 leadshine_motor_op: Leadshine_Motor_op, 
                 storage_mapping: dict, 
                 current_mapping: dict, 
                 coordinates: dict, 
                 logger: Optional[logging.Logger] = None) -> None:
        
        # initialize the operations
        self.axis_gripper_op = axis_gripper_op
        self.leadshine_motor_op = leadshine_motor_op
        self.logger = logger
        
        # initialize the mapping
        self.storage_mapping = storage_mapping
        self.current_mapping = current_mapping
        
        # get all the coordiantes for vials 
        self.coordinates = coordinates

    def move_bottle_to(self, bottle_idx: int, target_idx: int):
        """
        move bottle to the other index.

        Args:
            bottle_idx: bottle_index
            target_idx: target_index
        """
        # check the current position of the motor 
        if self.leadshine_motor_op.current_position[1] != self.coordinates["bottles"][bottle_idx]:
            self.axis_gripper_op.air_gripper(False)
            self.axis_gripper_op.actuator(True)
            self.leadshine_motor_op.move_to_position(1, self.coordinates["bottles"][bottle_idx])
        # grab the bottle
        self.axis_gripper_op.actuator(False)
        self.axis_gripper_op.air_gripper(True)
        self.axis_gripper_op.actuator(True)
        # release the bottle
        self.leadshine_motor_op.move_to_position(1, self.coordinates["bottles"][target_idx])
        self.axis_gripper_op.actuator(False)
        self.axis_gripper_op.air_gripper(False)
        self.axis_gripper_op.actuator(True)


    def filtration(self, 
                   reactor: str, 
                   _return: bool = True,
                   collect: bool = False, 
                   solvent: Optional[str] = None, 
                   waiting_time: float = 100*60):
        """
        filtration of the selected reactor.

        Args:
            wash: flag, if true, use the selected solvent to wash after filtation. Defaults to False.
            collect: flag, if true, collect the liquid after filtration. Defaults to False.
            solvent: the selected solvent. Defaults to None.
            waiting_time: the time in second to wait for the filtartion to finish.
        """
        # find the raw funnel
        raw_funnel = check_obj_status('funnel', mapping = self.current_mapping)
        raw_funnel_idx = self.current_mapping['Funnels'][raw_funnel]['slot_index']
        vial_idx = self.current_mapping["Vials"][reactor]["slot_index"]
        self.leadshine_motor_op.move_to_position(1, self.coordinates["bottles"][vial_idx])
        # filtration
        self.axis_gripper_op.prepare_funnel(raw_funnel_idx)
        self.axis_gripper_op.prepare_bottle()
        self.axis_gripper_op.dump_mixture(raw_funnel_idx)
        self.axis_gripper_op.return_bottle()
        # raise up funnel while filtration
        # self.axis_gripper_op.lean_funnel(raw_funnel_idx, waiting_time)
        # not lean: 
        self.axis_gripper_op.get_obj("liquid_accpters", raw_funnel_idx)
        self.axis_gripper_op.gasaxis.trap("z", self.axis_gripper_op.coordinates["liquid_accpters"][raw_funnel_idx][2] - 10)
        time.sleep(waiting_time)
        self.axis_gripper_op.place_obj("liquid_accpters", raw_funnel_idx)
        # wait for certain amount of time to finish the filtration process
        if _return:
            self.axis_gripper_op.return_funnel(raw_funnel_idx)
            self.current_mapping['Funnels'][raw_funnel]['solid'] = True
            # if to collect the solution from the bottle
            if collect:
                if solvent == None:
                    solvent = "H2O"
                # collect the solution after filtration
                self.leadshine_motor_op.move_to_position(1, self.axis_gripper_op.coordinates['bottles'][3 - vial_idx])
                self.axis_gripper_op.get_obj('feeder', 0)
                self.axis_gripper_op.place_obj('collect', raw_funnel_idx, False)
                self.axis_gripper_op.gasaxis.trap("x", 
                                                  self.axis_gripper_op.coordinates['collect'][raw_funnel_idx][0] - 17)
                self.axis_gripper_op.gasaxis.trap("z", 
                                                  self.axis_gripper_op.coordinates['collect'][raw_funnel_idx][2] + 28)
                self.axis_gripper_op.pump('collect', -200, 60)
                
                # wash the tube after collect the liquid
                self.axis_gripper_op.place_obj('solvent', 0, False)
                self.axis_gripper_op.pump(solvent, open_time = 15)
                pump = threading.Thread(target = self.axis_gripper_op.pump, 
                                        args = ("air", 200, 10))
                move_waste = threading.Thread(target = self.leadshine_motor_op.move_to_position, 
                                              args = (1, self.axis_gripper_op.coordinates['bottles'][2 + vial_idx]))
                pump.start()
                move_waste.start()
                pump.join()
                move_waste.join()
                self.axis_gripper_op.pump('collect', -200, 80)
                self.axis_gripper_op.place_obj('feeder', 0, True)
            else:
                pass # to waste and do nothing

        return raw_funnel_idx