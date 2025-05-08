from .base import BaseDevice
import serial
import logging
import time

class PeristalticPump(BaseDevice):

    def __init__(self, ser: serial.Serial, slave, logger: logging.Logger):
        """
        The code can control M1-21C runze driver.

        Args:
            ser: serial communication
            slave: the device num of driver
            logger: logger
        """
        super().__init__(ser, slave, logger)
        self.set_commands_dict('PeristalticPump')

    def set_dynamic_speed(self, speed: int = 100):
        """
        Set_dynamic_speed.

        Args:
            speed: the speed of spin, unit: rpm. Defaults to 100.
        """
        self.send_message("set_dynamic_speed", speed)

    def pump_on(self, speed: int = 100, feedback: bool = True): 
        """
        Open pump by giving speed value to the driver.

        Args:
            speed: the speed of pump. Defaults to 100.
            feedback: feedback trigger. Defaults to True.
        """
        if speed: 
            self.set_dynamic_speed(abs(speed))
        if speed >= 0:
            self.send_message('clockwise_continus', 0)
        else:
            self.send_message('counterclockwise_continus', 0)
        self.logger.info(f"pump_on, current speed is {speed}.")
        if feedback:
            if not self.feedback('motor_sts', 4):
                self.logger.warning(f"pump_on failed.")
                raise SyntaxError(f"pump_on failed.")
            else: 
                return True
        
    def pump_off(self, feedback: bool = True):
        """
        Turn off the pump.

        Args:
            feedback: feedback trigger. Defaults to True.

        """
        self.send_message("forced_stop", 0)
        self.logger.info("pump_off, current speed is 0.")
        if feedback:
            if not self.feedback('motor_sts', 0):
                self.logger.warning(f"pump_off failed.")
                raise SyntaxError(f"pump_off failed.")
            else: 
                return True
            
    def pump_liquid(self, speed: int, pump_time: float):
        """
        Pump quantitative liquid by control the speed of pump, the opening time of pump.

        Args:
            speed: the speed of pump, unit: rpm.
            pump_time: the opening time of pump.
        """
        self.pump_on(speed)
        time.sleep(pump_time)
        self.pump_off()