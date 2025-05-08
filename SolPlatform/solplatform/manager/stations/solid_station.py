import yaml
import logging
from copy import copy
from ..utility import *
from ..operations import MG400_op, XPR_balance_op, Leadshine_Motor_op
import time 

class SolidStation:
    """
    The operations of SolidStation, 
    include: add_solid.
    """
    def __init__(self, 
                 XPR_balance_op: XPR_balance_op, 
                 MG400_op: MG400_op, 
                 moving_stage_op: Leadshine_Motor_op, 
                 mapping: dict, 
                 storage_mapping: dict, 
                 current_mapping: dict, 
                 coordinates: dict, 
                 logger: logging.Logger = None) -> None:
        """
        initialize the platform
        Args:
            XPR_balance_op: the operation of XPR_balance
            MG400_op: the operation of dobot_mg400
            moving_stage_op: the oparation of the motor
            head_vial_mapping_path: the path of mapping
            mapping: the mapping of vial, cap, head
            storage_mapping: the storage mapping of vial, cap, head
            current_mapping: the current mapping of vial, cap, head
            positions: a dict contains corrdinates of solidstation
            logger: logger
        """
        
        # define the original mapping and the current mapping
        self.mapping = mapping
        self.storage_mapping = storage_mapping
        self.current_mapping = current_mapping
        # initialize the logger
        self.logger = logger
        # initialize the positions
        self.coordinates = coordinates
        # initialize the operations out of the devices
        self.XPR_balance_op = XPR_balance_op
        self.MG400_op = MG400_op
        self.moving_stage_op = moving_stage_op
    
    def _add_solid(self, reactor: str, solid: list, quantity: list, tolerance: list):
        """
        add solid to a reactor
        Args:
            reactor: the name of the reactor
            solid: array, the names of the solids
            quantity: array, the mass of the solids in mg 
            tolerance: array, the percentage of tolerance of each solids
        """
        for w in quantity:
            if w < 0 :
                raise ValueError("Substance weight must not smaller than 0!")
        # wake up the balance and open the right door
        self.XPR_balance_op.open_door()
        data_total = []
        # begin to place ths dosing head one by one
        for index in range(len(solid)):
            head_location = self.current_mapping["Heads"][solid[index]]
            # check if there is any dosing head on balance
            balance_head = check_obj_status('head', 'balance', 0, self.current_mapping)
            
            # move the dosing head according
            if balance_head == False: # there is no head in balance
                if head_location["head_plates"] == 0:
                    # move the dosing head to the balance 
                    self.MG400_op.head_holder_to_balance(head_location["slot_index"])
                    self.current_mapping["Heads"][solid[index]]["head_plates"] = "balance"
                    self.current_mapping["Heads"][solid[index]]["slot_index"] = 0
                else:
                    raise ValueError("the dosing head has to be in head_plates 0! (will be extended in future version)")
            # there is a head
            else:
                # if its the head for the solid, do nothing 
                if balance_head == solid[index]:
                    pass
                # it is not the head for the solid, remove it to its original location and move another head to the balance 
                else:
                    # move away the head on the balance
                    self.MG400_op.head_balance_to_holder(self.storage_mapping["Heads"][balance_head]["slot_index"])
                    self.current_mapping["Heads"][balance_head] = copy(self.storage_mapping["Heads"][balance_head])
                    
                    # move in the head to the balance
                    self.MG400_op.head_holder_to_balance(head_location["slot_index"])
                    self.current_mapping["Heads"][solid[index]]["head_plates"] = "balance"
                    self.current_mapping["Heads"][solid[index]]["slot_index"] = 0 
            # dispense the solid and get the results
            time.sleep(5)
            data = self.XPR_balance_op.dispense(solid[index], quantity[index], tolerance[index])
            data_total.append(data)

        return data_total
    
    # def transfer_vial_to_LS(self, reactor):
    #     """
    #     Transfer a vial from solid station to liquid_station_init
    #     Args:
    #         reactor: the name of reactor
    #     """
    #     # get the information of the vial 
    #     vial_info = self.current_mapping["Vials"][reactor]
    #     # home the motor
    #     self.moving_stage_op.home("SolidStation")
    #     # if we are transferring vial from the balance, open it 
    #     if vial_info["bottle_plate"] == "balance":
    #         self.XPR_balance_op.open_door()
    #         self.MG400_op.PullBottleToIntermediate()
    #     # if we are transferring from the plate directly 
    #     else:
    #         self.MG400_op.MoveBottleToLS(vial_info["bottle_plate"], vial_info["slot_index"])
    #     self.moving_stage_op.move_to_position("SolidStation", self.positions["MovingStage"])
    #     self.current_mapping["Vials"][reactor]["bottle_plate"] = "liquid_station_init"
    #     self.current_mapping["Vials"][reactor]["slot_index"] = 0