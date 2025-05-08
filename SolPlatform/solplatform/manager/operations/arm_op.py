from Dobot_Arms import MG400
from dh_gripper import Gripper
from typing import Optional
import time
import numpy as np
import logging


class MG400_op:
    """
    Include the operations of dobot_mg400.
    Operations:
        Dosing_head moving
        Bottle moving
    """

    def __init__(
        self,
        mg400: MG400,
        pgse: Gripper,
        coordinates: Optional[dict] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        initialize the arm operation
        Args:
            mg400: an MG400 object that is responsible for the communication with the dobot mg400 arm
            pgse:  an Gripper object that is responsible for the communication with the dh_pgse gripper
            config: a dict containing the information of the corrdinates of solidstation
            logger: logger
        """
        # initialize the arm
        self.mg400 = mg400
        self.coordinates = coordinates
        self.initial_param = coordinates["Initial_Param"]
        self.Holder_Param = self.coordinates["Holder_Param"]
        self.Dosing_Head_Coordinates = self.coordinates["Dosing_Head_Coordinates"]
        self.Bottle_Coordinates = self.coordinates["Bottle_Coordinates"]
        self.Initial_Position = self.coordinates["Initial_Position"]
        self.Dosing_Head_Route = self.coordinates["Dosing_Head_Route"]
        self.Bottle_Balance_Route = self.coordinates["Bottle_Balance_Route"]
        self.Bottle_LS_Route = self.coordinates["Bottle_LS_Route"]
        self.mg400.initialize_robot(**self.initial_param)
        # initialize the pgse gripper
        self.pgse = pgse
        self.pgse.initialization()
        # set up the default speed
        self.mg400.SetSpeedJ(50)
        self.mg400.SetSpeedL(50)
        # initialize the logger and the current location
        self.current_position = self.mg400.current_actual
        self.logger = logger

    def move_to_positions(self, positions: list):
        """
        move to a series of position in sequence
        Args:
            positions: the route of arm
        """
        for position in positions:
            self.mg400.MoveL(position)
            self.current_position = position
            time.sleep(0.5)
        time.sleep(1)

    def reset_origin(self, type: str):
        """
        move to the origin position depend on the chosen type
        Args:
            type: the operation type of the arm, e.g. 'head' or 'bottle'
        """
        # judge which process is going to be done, and go to the reset point
        if self.current_position in self.Bottle_LS_Route:
            self.move_to_positions(self.Bottle_Balance_Route[:3][::-1])
        self.mg400.MoveL(self.Initial_Position[type])
        time.sleep(1)

    def head_holder_to_balance(self, dosing_head_idx: int, speed: int = 50):
        """
        place the dosing head on the balance
        Args:
            dosing_head_idx: the index of dosing head, which correspnods to its location
            speed: the speed of the arm
        """
        y_offset, z_offset, head_range = self.Holder_Param["dosing_head_holder"]
        if dosing_head_idx < head_range[1] and dosing_head_idx >= head_range[0]:
            # set speed
            if speed:
                self.mg400.SetSpeedL(speed)
                self.mg400.SetSpeedJ(speed)
            # operations:
            # open the clamp
            time.sleep(1)
            self.pgse.set_site(1000)
            time.sleep(1)
            # move to the initial point
            self.reset_origin('head')
            # move to the dosing head storage
            offsets = np.array([[0, y_offset, 0, 0], [0, 0, 0, 0]])
            positions = [
                list(np.array(self.Dosing_Head_Coordinates[dosing_head_idx]) + offset)
                for offset in offsets
            ]
            self.move_to_positions(positions)
            # close the clamp
            self.pgse.set_site(0)
            time.sleep(1)
            # raise up the dosing head a bit
            offsets = np.array([[0, 0, z_offset, 0], [0, y_offset, z_offset, 0]])
            positions = [
                list(np.array(self.Dosing_Head_Coordinates[dosing_head_idx]) + offset)
                for offset in offsets
            ]
            self.move_to_positions(positions)
            # move to the balance
            self.reset_origin('head')
            self.move_to_positions(self.Dosing_Head_Route)
            # open the clamp
            self.pgse.set_site(1000)
            time.sleep(1)
            # move alway from balance
            positions = self.Dosing_Head_Route[::-1]
            self.move_to_positions(positions)
            # move to the initial point
            self.reset_origin('head')
        else:
            raise ValueError(
                f"dosing_head_idx should be smaller than 30 and larger/equal to 0. current value:{dosing_head_idx}"
            )

    def head_balance_to_holder(self, dosing_head_idx: int, speed: int = 50):
        """
        place the dosing head back to the holder from the balance
        Args:
            dosing_head_idx: the index of dosing
            speed: the speed of the arm
        """
        y_offset, z_offset, head_range = self.Holder_Param["dosing_head_holder"]
        if dosing_head_idx < head_range[1] and dosing_head_idx >= head_range[0]:
            # set speed
            if speed:
                self.mg400.SetSpeedL(speed)
                self.mg400.SetSpeedJ(speed)
            # Operation:
            # open the clamp
            self.pgse.set_site(1000)
            time.sleep(1)
            # move to the initial point
            self.reset_origin('head')
            # move to the balance
            self.move_to_positions(self.Dosing_Head_Route)
            # close the clamp
            self.pgse.set_site(0)
            # move alway from balance
            self.move_to_positions(self.Dosing_Head_Route[::-1])
            # approach the dosing head
            self.reset_origin('head')
            offsets = np.array(
                [[0, y_offset, z_offset, 0], [0, 0, z_offset, 0], [0, 0, 0, 0]]
            )
            positions = [
                list(np.array(self.Dosing_Head_Coordinates[dosing_head_idx]) + offset)
                for offset in offsets
            ]
            self.move_to_positions(positions)
            time.sleep(0.5)
            # open the clamp
            self.pgse.set_site(1000)
            time.sleep(1)
            # move to the front side of the dosing head
            offsets = np.array([[0, y_offset, 0, 0]])
            positions = [
                list(np.array(self.Dosing_Head_Coordinates[dosing_head_idx]) + offset)
                for offset in offsets
            ]
            self.move_to_positions(positions)
            # move to the initial point
            self.reset_origin("head")
        else:
            raise ValueError(
                f"dosing_head_idx should be smaller than 30 and larger/equal to 0. current value:{dosing_head_idx}"
            )

    def bottle_plate_to_balance(
        self, plate_name: str, bottle_idx: int, speed: int = 50
    ):
        """
        place the bottle into the balance
        Args:
            plate_num: the number of bottle plate
            bottle_idx: the index of bottle
            speed: the speed of the arm
        """
        z_offset, bottle_capacity = self.Holder_Param[plate_name]
        if bottle_idx in range(bottle_capacity[0], bottle_capacity[1], 1) and (
            plate_name in self.Bottle_Coordinates.keys()
        ):
            # set speed
            if speed:
                self.mg400.SetSpeedL(speed)
                self.mg400.SetSpeedJ(speed)
            # set plate initial point and coordinate system
            # operations:
            # open the clamp:
            self.pgse.set_site(1000)
            time.sleep(1)
            # move to the initial point
            self.reset_origin('bottle')
            # move to the position of target bottle
            offsets = np.array([[0, 0, z_offset, 0], [0, 0, 0, 0]])
            positions = [
                list(np.array(self.Bottle_Coordinates[plate_name][bottle_idx]) + offset)
                for offset in offsets
            ]
            self.move_to_positions(positions)
            # close the clamp
            time.sleep(0.5)
            self.pgse.set_site(0)
            # move to the plate initial point
            offsets = np.array([[0, 0, z_offset, 0]])
            positions = [
                list(np.array(self.Bottle_Coordinates[plate_name][bottle_idx]) + offset)
                for offset in offsets
            ]
            self.move_to_positions(positions)
            # move to the inside of balance
            self.move_to_positions(self.Bottle_Balance_Route)
            time.sleep(0.5)
            # open the clamp
            self.pgse.set_site(1000)
            time.sleep(1)
            # move to the outside of balance
            self.move_to_positions(self.Bottle_Balance_Route[::-1])
        else:
            raise ValueError(
                f"bottle_idx should be smaller than 25 and larger/equal to 0. current value:{bottle_idx}"
            )

    def bottle_balance_to_LS(self, speed: int = 50):
        """
        move bottle from balance to liquid station
        Args:
            speed: the speed of the arm
        """
        # set speed
        if speed:
            self.mg400.SetSpeedL(speed)
            self.mg400.SetSpeedJ(speed)
        # operations:
        # open the clamp
        self.pgse.set_site(1000)
        time.sleep(1)
        # move to the balance
        self.move_to_positions(self.Bottle_Balance_Route)
        time.sleep(0.5)
        # close the clamp
        self.pgse.set_site(0)
        # move to the outside of the balance
        self.move_to_positions(self.Bottle_Balance_Route[::-1][:4])
        # move to the liquid station
        self.move_to_positions(self.Bottle_LS_Route)
        time.sleep(0.5)
        # open the clamp
        self.pgse.set_site(1000)
        time.sleep(1)
        # move back to the initial point
        self.move_to_positions(self.Bottle_LS_Route[::-1])

    def bottle_plate_to_LS(self, plate_name: str, bottle_idx: int, speed: int = 50):
        """
        move target bottle which is on plate_0 or plate_1 to liquid station
        Args:
            plate_num: the number of bottle plate
            bottle_idx: the index of bottle
            speed: the speed of the arm
        """
        z_offset, bottle_range = self.Holder_Param[plate_name]
        if bottle_idx in range(bottle_range[0], bottle_range[1], 1) and (
            plate_name in self.Bottle_Coordinates.keys()
        ):
            # set speed
            if speed:
                self.mg400.SetSpeedL(speed)
                self.mg400.SetSpeedJ(speed)
            # operations:
            # open the clamp
            self.pgse.set_site(1000)
            time.sleep(1)
            # move to the initial point
            self.reset_origin('bottle')
            # move to the position of target bottle
            offsets = np.array([[0, 0, z_offset, 0], [0, 0, 0, 0]])
            positions = [
                list(np.array(self.Bottle_Coordinates[plate_name][bottle_idx]) + offset)
                for offset in offsets
            ]
            self.move_to_positions(positions)
            # close the clamp
            time.sleep(0.5)
            self.pgse.set_site(0)
            # move to the plate initial point
            offsets = np.array([[0, 0, z_offset, 0]])
            positions = [
                list(np.array(self.Bottle_Coordinates[plate_name][bottle_idx]) + offset)
                for offset in offsets
            ]
            self.move_to_positions(positions)
            # move to the liquid station
            positions = self.Bottle_Balance_Route[:3] + self.Bottle_LS_Route
            self.move_to_positions(positions)
            time.sleep(0.5)
            # open the clamp
            self.pgse.set_site(1000)
            time.sleep(1)
            # move back to the initial point
            self.move_to_positions(self.Bottle_LS_Route[::-1])
        else:
            raise ValueError(
                f"bottle_idx should be smaller than 25 and larger/equal to 0. current value:{bottle_idx}"
            )

    def bottle_LS_to_plate_or_balance(
        self, plate_name: str, bottle_idx: Optional[int] = None, speed: int = 50
    ):
        """
        transfer bottle from liquidstation to the holder on the solidstation, e.g. plate_0, plate_1, balance
        Args:
            plate_name: the name of target plate, e.g. plate_0, plate_1, balance
            bottle_idx: the index of target slot
            speed: the speed of the mg400 arm
        """
        bottle_range = self.Holder_Param["plate_0"][1]
        # check if moving the bottle to balance
        to_balance = plate_name == "balance"
        # check if the index is allowed
        if to_balance:
            pass
        elif bottle_idx in range(bottle_range[0], bottle_range[1], 1) and (
            plate_name in self.Bottle_Coordinates.keys()
        ):
            pass
        else:
            raise ValueError(
                f"{plate_name} with bottle_idx of {bottle_idx} is not supported"
            )
        # pass the sanity check, perform transfer below
        # set speed
        if speed:
            self.mg400.SetSpeedL(speed)
            self.mg400.SetSpeedJ(speed)
        # operations:
        # open the clamp
        self.pgse.set_site(1000)
        time.sleep(1)
        # move to the initial point
        if self.current_position not in self.Bottle_LS_Route:
            self.reset_origin('bottle')
            positions = self.Bottle_Balance_Route[:3]
            self.move_to_positions(positions)
        # move to liquid station
        self.move_to_positions(self.Bottle_LS_Route)
        # close the clamp
        time.sleep(0.5)
        self.pgse.set_site(0)
        # move back to the initial point
        self.move_to_positions(self.Bottle_LS_Route[::-1])
        if to_balance:
            # move to the inside of balance
            self.move_to_positions(self.Bottle_Balance_Route[2:])
            time.sleep(0.5)
            # open the clamp
            self.pgse.set_site(1000)
            time.sleep(1)
            # move to the outside of balance
            self.move_to_positions(self.Bottle_Balance_Route[::-1])
        else:
            z_offset, bottle_range = self.Holder_Param[plate_name]
            # move to origin point of bottle plate
            self.reset_origin('bottle')
            # move to the position of target bottle
            offsets = np.array([[0, 0, z_offset, 0], [0, 0, 0, 0]])
            positions = [
                list(np.array(self.Bottle_Coordinates[plate_name][bottle_idx]) + offset)
                for offset in offsets
            ]
            self.move_to_positions(positions)
            # open the clamp
            time.sleep(0.5)
            self.pgse.set_site(1000)
            time.sleep(1)
            # move to the top of the bottle
            offsets = np.array([[0, 0, z_offset, 0]])
            positions = [
                list(np.array(self.Bottle_Coordinates[plate_name][bottle_idx]) + offset)
                for offset in offsets
            ]
            self.move_to_positions(positions)
            self.reset_origin('bottle')

    def bottle_balance_to_plate(
        self, plate_name: str, bottle_idx: int, speed: int = 50
    ):
        """
        transfer bottle from balance to the bottle plate e.g. plate_0, plate_1
        Args:
            plate_name: the name of target plate, e.g. plate_0, plate_1
            bottle_idx: the index of target slot
            speed: the speed of the mg400 arm
        """
        # set speed
        if speed:
            self.mg400.SetSpeedL(speed)
            self.mg400.SetSpeedJ(speed)
        # operations:
        # open the clamp
        self.pgse.set_site(1000)
        time.sleep(1)
        # move to the initial point
        self.reset_origin('bottle')
        # move to the balance
        self.move_to_positions(self.Bottle_Balance_Route)
        time.sleep(0.5)
        # close the clamp
        self.pgse.set_site(0)
        # move to the outside of the balance
        self.move_to_positions(self.Bottle_Balance_Route[::-1])
        # load the param of the bottle_holder
        z_offset, bottle_range = self.Holder_Param[plate_name]
        if bottle_idx in range(bottle_range[0], bottle_range[1], 1) and (
            plate_name in self.Bottle_Coordinates.keys()
        ):
            # move to the target plate and target slot
            offsets = np.array([[0, 0, z_offset, 0], [0, 0, 0, 0]])
            positions = [
                list(np.array(self.Bottle_Coordinates[plate_name][bottle_idx]) + offset)
                for offset in offsets
            ]
            self.move_to_positions(positions)
            # open the clamp
            time.sleep(0.5)
            self.pgse.set_site(1000)
            time.sleep(1)
            # move to the top of the current location
            offsets = np.array([[0, 0, z_offset, 0]])
            positions = [
                list(np.array(self.Bottle_Coordinates[plate_name][bottle_idx]) + offset)
                for offset in offsets
            ]
            self.move_to_positions(positions)
            # move to the initial point
            self.reset_origin('bottle')
        else:
            raise ValueError(
                f"bottle_idx should be smaller than 25 and larger/equal to 0. current value:{bottle_idx}"
            )

    def bottle_plate_to_plate(
        self,
        plate_name_0: str,
        bottle_idx_0: int,
        plate_name_1: str,
        bottle_idx_1: int,
        speed: int = 50,
    ):
        """
        transfer the bottle among the plates.

        Args:
            plate_name_0: the name of the initial plate.
            bottle_idx_0: the bottle index.
            plate_name_1: the target plate on solid station.
            bottle_idx_1: the target index.
            speed: the speed of the arm. Defaults to 50.
        """
        # set speed
        if speed:
            self.mg400.SetSpeedL(speed)
            self.mg400.SetSpeedJ(speed)
        # Operations: 
        # get the bottle
        z_offset_0, bottle_range_0 = self.Holder_Param[plate_name_0]
        z_offset_1, bottle_range_1 = self.Holder_Param[plate_name_1]
        if (
            bottle_idx_0 in range(bottle_range_0[0], bottle_range_0[1], 1)
            and (plate_name_0 in self.Bottle_Coordinates.keys())
        ) and (
            bottle_idx_1 in range(bottle_range_1[0], bottle_range_1[1], 1)
            and (plate_name_1 in self.Bottle_Coordinates.keys())
        ):

            self.pgse.set_site(1000)
            time.sleep(1)
            # move to the initial point
            self.reset_origin('bottle')
            # move to the position of target bottle
            offsets = np.array([[0, 0, z_offset_0, 0], [0, 0, 0, 0]])
            positions = [list(np.array(self.Bottle_Coordinates[plate_name_0][bottle_idx_0]) + offset) for offset in offsets]
            self.move_to_positions(positions)
            # close the clamp
            time.sleep(0.5)
            self.pgse.set_site(0)
            # move to the top of the bottle
            offsets = np.array([[0, 0, z_offset_0, 0]])
            positions = [list(np.array(self.Bottle_Coordinates[plate_name_0][bottle_idx_0]) + offset) for offset in offsets]
            self.move_to_positions(positions)
            # place the bottle
            # move to the position of target bottle
            offsets = np.array([[0, 0, z_offset_1, 0], [0, 0, 0, 0]])
            positions = [list(np.array(self.Bottle_Coordinates[plate_name_1][bottle_idx_1]) + offset) for offset in offsets]
            self.move_to_positions(positions)
            # open the clamp
            time.sleep(0.5)
            self.pgse.set_site(1000)
            time.sleep(1)
            # move to the top of the bottle
            offsets = np.array([[0, 0, z_offset_1, 0]])
            positions = [list(np.array(self.Bottle_Coordinates[plate_name_1][bottle_idx_1]) + offset) for offset in offsets]
            self.move_to_positions(positions)
            # move back to the origin point
            self.reset_origin('bottle')
        else:
            raise ValueError(
                f"bottle_idx should be smaller than 25 and larger/equal to 0. idx_0 current value:{bottle_idx_0}; idx_1 current value:{bottle_idx_1}"
            )