from leadshine_driver import LeadShine_Controller
from typing import Optional
import logging

class Leadshine_Motor_op:
    """
    Include the operations of motors
    Operations:
        home, move_to_position
    """
    def __init__(self, 
                 motor_0: Optional[LeadShine_Controller] = None,
                 motor_1: Optional[LeadShine_Controller] = None, 
                 logger: logging.Logger = None):
        """
        initialize the operation of motor

        Args:
            motor: a ArdunioStepper object that is responsible for the communication with 28 stepper motor
            logger: logger
        """
        # initialize the motor
        self.motor_0 = motor_0
        self.motor_1 = motor_1
        self.current_position = {
            0: self.motor_0.current_position, 
            1: self.motor_1.current_position
        }
        self.home(0)
        self.home(1)
        self.logger = logger
        
    def update_current_position(self):
        self.current_position[0] = self.motor_0.current_position
        self.current_position[1] = self.motor_1.current_position

    def home(self, motor_index: int):
        """
        home the moving_stage

        Args:
            motor_index: the index of motor.
        """
        if motor_index == 0: 
            self.motor_0.datum()
        elif motor_index == 1: 
            self.motor_1.datum()
        else:
            raise ValueError(f"the motor_index should be 0/1, current value {motor_index}.")
        self.update_current_position()

    def move_to_position(self, motor_index: int, position: int, speed: Optional[float] = None):
        """
        move the moving_stage to target position

        Args:
            motor_index: the index of motor.
            position: the target position
        """
        if motor_index == 0: 
            self.motor_0.absolute_move(position, speed)
        elif motor_index == 1: 
            self.motor_1.absolute_move(position, speed)
        else:
            raise ValueError(f"the motor_index should be 0/1, current value {motor_index}.")
        self.update_current_position()
        