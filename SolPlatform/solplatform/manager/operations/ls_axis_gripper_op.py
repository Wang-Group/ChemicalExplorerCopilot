import logging
import time
from ..utility import *
from typing import Optional
from copy import copy
from dh_gripper import Gripper
from runze_driver import Injector
from zmotion import AxisMotion

DEFAULT_SPEED = 5/6
LOW_SPEED = 0.2

class LS_Axis_Gripper_op:
    """
    Include the operations of zmotion multi-axis system, dh-gripper(rgi30, pge50) and runze-injector.

    Operations:
        Get object from origin location on liquidstation.
        Place object to target location on liquidstation.
    """
    def __init__(
            self, 
            axismotion: AxisMotion = None, 
            rgi30: Gripper = None, 
            pge50: Gripper = None, 
            injector: Injector = None, 
            config: dict = None, 
            logger: Optional[logging.Logger] = None):
        """
        Initialize the multi-axis and gripper operation.

        Args: 
            axismotion: an Axismotion object that is responsible for the communication with the muti-axis system
            rgi30: a Gripper object that is responsible for the communication with rgi30 gripper
            pge50: a Gripper object that is responsible for the communication with pge50 gripper
            config: a dict containing the information of the locations
            logger: logger
        """

        self.axismotion = axismotion
        self.rgi30 = rgi30
        self.pge50 = pge50
        self.injector = injector
        self.injector.set_dynamic_speed(DEFAULT_SPEED)
        self.injector.initialization()
        self.info = config["info"]
        self.coordinates = config["coordinates"]
        self.logger = logger
        # datum the axis
        self.axismotion.datum_xyz()
        self.axismotion.output_trigger("fans", True)
        # initialize the grippers
        self.rgi30.initialization()
        self.rgi30.set_site(800)
        self.pge50.initialization()

    def _reset_origin(self):
        """
        Move axis quickly to the origin point.
        """
        aquire(self.axismotion)
        self.axismotion._move_xyz([0, 0, 0, 0])
        release(self.axismotion)

    def _reset_axis_z(self, height: float = 0):
        """
        Move axis z quickly to the origin point.
        """
        aquire(self.axismotion)
        self.axismotion._absolute_move("z1", height)
        self.axismotion._absolute_move("z2", height)
        release(self.axismotion)

    def _get_pipette_tip(self, tip_idx: int):
        """
        Get the tip by moving injector on the selcted tip.

        Args:
            tip_idx: _description_
        """
        aquire(self.axismotion)
        self.axismotion._move_xyz(self.coordinates["pipette_tips"][tip_idx])
        release(self.axismotion)

    def _get_obj(self, target_plate: str, idx: int, z1_offset: float = 0, z2_offset: float = 0):
        """
        Get object on the liquidstation.

        Args:
            target_plate: the plate of the target object in 
            idx: the target slot index
        """
        aquire(self.axismotion)
        # open rgi30 if there is no things on the gripper
        if self.rgi30.feedback("clamp_sts") != 2:
            self.rgi30.set_site(800)
        # move to the location of target bottle
        target_coordinate = copy(self.coordinates[target_plate][idx])
        target_coordinate[2] = target_coordinate[2] - z1_offset
        target_coordinate[3] = target_coordinate[3] - z2_offset
        self.axismotion._move_xyz(target_coordinate)
        release(self.axismotion)
        # close rgi30
        self.rgi30.set_site(0)
        # if the target plate is pge50_platform, open pge50, else return True
        if target_plate == "pge50_platform":
            self.pge50.set_site(1000)
        else:
            return True

    def _place_obj(self, 
                   target_plate: str, 
                   idx: int, 
                   open_pge50: bool = True, 
                   open_rgi30: bool = True, 
                   z1_offset: float = 0, 
                   z2_offset: float = 0):
        """
        Place object to target location on liquidstation which is already on rgi30 gripper.

        Args: 
            target_plate: the plate of target destinaton
            idx: the slot index of target destination
        """    
        # move to the target location
        aquire(self.axismotion)
        if target_plate == "pge50_platform":
            if open_pge50:
                self.pge50.set_site(1000)
        target_coordinate = copy(self.coordinates[target_plate][idx])
        target_coordinate[2] = target_coordinate[2] - z1_offset
        target_coordinate[3] = target_coordinate[3] - z2_offset
        self.axismotion._move_xyz(target_coordinate)
        release(self.axismotion)
        if target_plate == "pge50_platform":
            self.pge50.set_site(0)
        # open rgi30 while needed
        if open_rgi30:
            self.rgi30.set_site(800)

    def _close_bottle(self, cap_idx: int, cap_plate: str = "cap_holders"):
        """
        Close the bottle while the bottle is already on pge50_platform.

        Args:
            cap_idx: the target cap index
            cap_plate: the target cap holder, normally is 'cap_holders'
        """
        # close pge50 and open rgi30
        self.pge50.set_site(0)
        self.rgi30.set_site(800)
        # get cap and move to the top of bottle
        self._get_obj(cap_plate, cap_idx)
        self._place_obj("pge50_platform", 0, False, False)
        # rotate rgi30 in order to close the cap
        self.rgi30.set_rotation_angle(-1080)

    def _open_bottle(self, cap_idx: int, cap_plate: str = "cap_holders", spin_angle: int = 800):
        """
        Open the bottle while the bottle is already on pge50_platform.

        Args:
            cap_idx: the storge index of the cap on the bottle
            cap_plate: the target cap holder, normally is 'cap_holders'
            spin_angle: the spin angle of gripper when open bottle.
        """
        # close rgi30
        self.rgi30.set_site(0)
        # close pge50
        self.pge50.set_site(0)
        # rotate rgi30 in order to open the cap
        self.rgi30.set_rotation_angle(spin_angle)
        time.sleep(0.5)
        self.axismotion._absolute_move("z1", 0)
        self.rgi30.set_rotation_angle(900 - spin_angle)
        # place cap to the target location (cap_idx)
        self._place_obj(cap_plate, cap_idx)

    def _push_actuator(self, wait_time: float = 5.0):
        """ 
        Use zmotion controller IO module to control relay to push tip on injector.

        Args:
            wait_time: the time of high signal status.
        """
        self.axismotion.output_trigger('actuator_relay', True)
        time.sleep(wait_time)
        self.axismotion.output_trigger('actuator_relay', False)
        time.sleep(wait_time)

    def _magnetic_stir(self, wait_time: float = 5.0):
        """ 
        Use zmotion controller IO module to control relay to magnetic stir.

        Args:
            wait_time: the time of high signal status.
        """
        self.axismotion.output_trigger('magnetic_stir', True)
        time.sleep(wait_time)
        self.axismotion.output_trigger('magnetic_stir', False)

    def _absorb_liquid(self, volume: float, speed: int = DEFAULT_SPEED):
        """
        Absorb_liquid by injector(please get the tip first!).

        Args:
            volume: _description_
        """
        self.injector.absorb(volume, speed)
        self.injector.set_dynamic_speed(DEFAULT_SPEED)

    def _inject_liquid(self, speed: int = DEFAULT_SPEED):
        """
        Inject liuqid the move axis_z2 to 0, after that, reset the position of injector.
        """
        aquire(self.axismotion)
        self.injector.injecting(speed, speed)
        self.axismotion._absolute_move("z2", 0)
        release(self.axismotion)
        self.injector.absorb(0, speed)
        self.injector.set_dynamic_speed(DEFAULT_SPEED)
        self.logger.info("inject succeed.")

    def _mix_liquid(self, volume: float, mix_frequency: int = 1,  speed: int = DEFAULT_SPEED):
        """
        Mix the liquid by absorb and inject the same volume, mix times can be input, default value is 1.

        Args:
            volume: the volue of mix. 
            mix_frequency: the mix times, default to 1.
        """
        self.injector.set_dynamic_speed(speed)
        for i in range(mix_frequency):
            self.injector.mix(volume)
        self.injector.set_dynamic_speed(DEFAULT_SPEED)