from .base import BaseDevice
import time
import serial
import logging


MODEL = {"SY-03B": {"max_step": 3000, 
                   "max_distance": 60, 
                   "lead": 6}, 
         "SY-08": {"max_step": 12000, 
                   "max_distance": 30, 
                   "lead": 1}, 
         "SY-06B": {"max_step": 6000, 
                   "max_distance": 60, 
                   "lead": 2}, 
         "SY-09-8-mL": {"max_step": 3840, 
                        "max_distance": 19.2, 
                        "lead":1}, 
         "SY-09-3-mL":{"max_step": 3600, 
                       "max_distance": 18, 
                       "lead": 1}
        }

class SyringePump(BaseDevice):

    def __init__(self, ser: serial.Serial, slave: int, model: str, volume: float, logger: logging.Logger):
        """
        Initialize some useful param of syringe_pump.

        Args:
            ser: serial connection
            slave: the slave of this device
            logger: Logger
            volume: the max volume of chosen injector
        """
        super().__init__(ser, slave, logger)
        self.volume = volume # the max volume of the injector
        self.set_commands_dict('SyringePump')
        self.max_step = MODEL[model]["max_step"] # unit: step
        self.max_distance = MODEL[model]["max_distance"] # unit: mm
        self.lead = MODEL[model]["lead"] # unit: mm

    def valve_restoration(self, feedback: bool = True):
        """
        Reset the switch valve on the syringe_pump.
        !!!ATTENTION: This function must be used before the forced_reset or pump_restoration.

        Args:
            feedback: Choose whether need feedback. Defaults to True.
        """
        self.send_message('valve_reset', 0)
        time.sleep(0.1)
        if feedback:
            self.feedback("motor_sts")
            current_channel = self.feedback('current_channel')
            if not self.feedback('current_channel', 15):
                self.logger.error(f"valve_restoration failed, current channel is {current_channel}.")
                raise ValueError(f"valve_restoration failed, current channel is {current_channel}.")
            else:
                self.logger.info(f"valve_restoration succeed, current channel is {current_channel}!")

    def pump_restoration(self, feedback: bool = True):
        """
        Reset the position of syringe_pump.

        Args:
            feedback: Choose whether need feedback. Defaults to True.
        """
        self.send_message('pump_reset', 0)
        time.sleep(0.1)
        if feedback:
            self.feedback("motor_sts")
            current_volume = self.feedback('get_position') / (self.max_step / self.volume)
            if not self.feedback('get_position', 0):
                self.logger.error(f"pump_restoration failed, current volume is {current_volume} mL.")
                raise ValueError(f"pump_restoration failed, current volume is {current_volume} mL.")
            else:
                self.logger.info("pump_restoration succeed, current volume is 0.")
                return True

    def forced_reset(self, feedback: bool = True):
        """
        Force to reset the position of syringe_pump.
        
        Args: 
            feedback: Choose whether need feedback. Defaults to True.
        """
        self.send_message('forced_reset',0)
        time.sleep(0.1)
        if feedback:
            self.feedback("motor_sts")
            current_volume = self.feedback('get_position') / (self.max_step / self.volume)
            if not self.feedback('get_position', 0):
                self.logger.error(f"pump_restoration failed, current volume is {current_volume} mL.")
                raise ValueError(f"pump_restoration failed, current volume is {current_volume} mL")
            else:
                self.logger.info("pump_restoration succeed, current volume is 0.")
                return True

    def move_to_absolute_position(self, absolute_volume: float, feedback: bool = True):
        """
        Move the motor to an absolute position.

        Args:
            absolute_volume: the volume created by moving motor, unit: mL
            feedback: Choose whether need feedback. Defaults to True.
        """
        step = round(absolute_volume  * self.max_step / self.volume)
        self.send_message('absolute_move', step)
        time.sleep(0.1)
        if feedback:
            self.feedback("motor_sts")
            current_step = self.feedback("get_position")
            current_volume = current_step / (self.max_step / self.volume)
            if not self.feedback("get_position", step):
                self.logger.info(f'move_to_absolute_position failed, current position is {current_step} step & {current_volume} mL.')
            else:
                self.logger.info(f'move_to_absolute_position succeed, current position is {current_step} step & {current_volume} mL.')
                return True
    
    def set_dynamic_speed(self, speed: float = 1.75):
        """
        Set the dynamic speed of the pump.

        Args:
            speed: the speed of motor, unit: mL/s. Defaults to 1.75.
        """
        rpm = round(speed / self.volume / (self.lead / self.max_distance) * 60) # 60 is 60 s/min
        self.send_message('set_dynamic_speed', rpm)
        time.sleep(0.1)
        self.logger.info(f"current_speed is {speed}.")

    def move_to_relative_position (self, volume: float):
        """
        move to relative position from current position.

        Args:
            volume: the moving volume value.
        """
        current_volume = self.feedback('get_position') / (self.max_step / self.volume)
        self.move_to_absolute_position(current_volume - volume)

    def open_valve(self):
        """
        For SY serial with "S", a solenoid was used.
        Open the valve.
        """
        self.send_message("valve_open", 1)

    def close_valve(self):
        """
        For SY serial with "S", a solenoid was used.
        Close the valve.
        """
        self.send_message("valve_close", 1)