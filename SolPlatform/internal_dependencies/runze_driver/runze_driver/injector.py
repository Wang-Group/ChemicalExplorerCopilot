import time
import logging
import serial
from typing import Optional
from .base import BaseDevice

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
                        "lead":2}, 
         "SY-09-3-mL":{"max_step": 3600, 
                       "max_distance": 18, 
                       "lead": 1}
        }

class Injector(BaseDevice):
    """
    A syringe pump acts as injector.

    Args:
        BaseDevice: runze base operations
    """
    def __init__(self, 
                 ser: serial.Serial, 
                 slave: int, 
                 model: str, 
                 max_tip_volume: int, 
                 volume: float = 5, 
                 logger: Optional[logging.Logger] = None):
        super().__init__(ser, slave, logger)

        self.max_step = MODEL[model]["max_step"] # max step 
        self.lead = MODEL[model]["lead"] # lead 
        self.max_distance = MODEL[model]["max_distance"] # max distance 
        self.volume = volume # max volume 
        self.max_tip_volume = max_tip_volume # max tip volume
        self.DEFULT_VOlUME = 0.5
        self.set_commands_dict('Injector')


    def initialization(self, feedback: bool = True):
        """
        Force to reset injector.

        Args:
            feedback: choice to get feedback or not. Defaults to True.

        """
        self.send_message("forced_reset", 0)
        time.sleep(0.1)
        if feedback:
            self.feedback("motor_sts")
            if not self.feedback("get_position", 0):
                self.logger.error("Injector initialization failed :( ")
                raise ValueError("Injector initialization failed :( ")
            else:
                self.logger.info("Injector initialization succeed :) ")
        self.absolute_move(self.DEFULT_VOlUME, feedback = feedback)
        
    
    def set_dynamic_speed(self, speed: float = (5/6)):
        """
        Set the speed of injector.

        Args:
            speed: the speed of injector, unit: mL/s. Defaults to 5/6 (SY-08-5mL).
        """
        rpm = round(speed / self.volume / (self.lead / self.max_distance) * 60)
        self.send_message("set_dynamic_speed", rpm)
        self.logger.info(f"current_speed is {speed} mL/s.")

    def absolute_move(self, position: float, speed: float = (5/6), feedback: bool = True):
        """
        Absolute move the pistons.

        Args:
            position: absolute position, unit: mL.
            speed: the speed of move, unit: mL/s. Defaults to 5/6(SY-08-5mL).
            feedback: choice to get feedback or not. Defaults to True. 
        """
        # see whether the position will bigger than the tip volume + defult volume
        if position > self.max_tip_volume + self.DEFULT_VOlUME:
            self.logger.error(f"position should not bigger than max tip volume, current value is {position}.")
            raise ValueError(f"position should not bigger than max tip volume, current value is {position}.")
        self.set_dynamic_speed(speed)
        step = round(position * (self.max_step / self.volume))
        # transfer step into param_0&1
        self.send_message("absolute_move", step)
        time.sleep(0.1)
        if feedback:
            self.feedback("motor_sts")
            current_position = self.feedback("get_position")/(self.max_step / self.volume)
            if not self.feedback("get_position", step):
                raise ValueError(f"the position is not so correct, set position is {position} mL, current position is {current_position} mL")
            else:
                self.logger.info("absolute_move succeed!")
                return True

    def absorb(self, volume: float, speed: int = (5/6), feedback: bool = True):
        """
        absorb the volumetric volume into the tip.

        Args:
            volume: the volume.
            speed: the speed of absorb. Defaults to (5/6).
            feedback: feedback trigger. Defaults to True.

        """
        self.absolute_move(volume + self.DEFULT_VOlUME, speed, feedback = False)
        if feedback:
            self.feedback("motor_sts")
            step = (volume + self.DEFULT_VOlUME) * (self.max_step / self.volume)
            current_volume = self.feedback("get_position") / (self.max_step / self.volume) - self.DEFULT_VOlUME 
            if not self.feedback("get_position", step):
                self.logger.warning(f"the absorbed volume is not so correct, set volume is {volume}, current volume is {current_volume}")
            else:
                self.logger.info("absorb succeed!")  
                return True

    def injecting(self, speed: float = (5/6), feedback: bool = True):
        """
        push all liquid out of tip, and piston not back to origin position.

        Args:
            speed: the speed of injecting. Defaults to (5/6).
            feedback: feedback trigger. Defaults to True.
        """
        self.set_dynamic_speed(speed)
        self.send_message("reset", 0)
        time.sleep(0.1)
        if feedback:
            self.feedback("motor_sts")
            current_volume = self.feedback("get_position") / (self.max_step / self.volume)
            if not self.feedback("get_position", 0):
                raise ValueError(f"injecting failed, current_volume is {current_volume}.")
            else:
                self.logger.info("injecting succeed!")
                return True
            
    def inject(self, speed: float = (5/6), feedback: bool = True):
        """
        push all liquid out of tip, and piston back to origin position.

        Args:
            speed: the speed of inject. Defaults to (5/6).
            feedback: feedback trigger. Defaults to True.
        """
        self.absolute_move(0, speed, feedback = feedback)
        self.absolute_move(self.DEFULT_VOlUME, feedback = feedback)
        self.logger.info("inject succeed!")
        return True

    def mix(self, volume: float, speed: float = (5/6), feedback: bool = True): 
        """
        mix liquid by absorb selected volume and push out liquid.

        Args:
            volume: volume of mixing
            speed: speed of mixing. Defaults to (5/6).
            feedback: feedback trigger. Defaults to True.
        """
        self.absolute_move(volume + self.DEFULT_VOlUME, speed, feedback)
        time.sleep(0.1)
        self.absolute_move(self.DEFULT_VOlUME, speed, feedback)
        self.logger.info("mix succeed!")

    # FIXME
    def rinse(self):
        """
        this func will be fixed when needed.
        """
        pass
