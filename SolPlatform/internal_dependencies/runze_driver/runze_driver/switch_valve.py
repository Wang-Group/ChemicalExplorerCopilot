from .base import BaseDevice
import serial
import logging
import time


class SwitchValve(BaseDevice):

    def __init__(self, 
                 ser: serial.Serial, 
                 slave: int, 
                 channel_num: int,
                 model: str = "SV-07", 
                 logger: logging.Logger = None):
        """
        

        Args:
            ser: the serial connection
            slave: the device num of valve
            channel_num: channel num of valve
            model: the valve model. Defaults to "SV-07".
            logger: logger. Defaults to None.
        """
        super().__init__(ser, slave, logger)
        self.set_commands_dict('SwitchValve')
        self.channel_num = channel_num
        self.model = model

    def restoration(self, feedback: bool = True):
        """
        The initialization of valve.
        """
        # different model with different feedback position.
        if "B" in self.model:
            orgin_point = 1
        elif self.model == "SV-01":
            orgin_point = 0
        else: 
            orgin_point = self.channel_num * 256 + 1
        self.send_message('reset', 0)
        time.sleep(0.1)
        if feedback:
            self.feedback("motor_sts")
            if not self.feedback('current_channel', orgin_point):
                print(self.feedback('current_channel'))
                self.logger.error("restoration failed.")
                raise ValueError("restoration failed.")
            else:
                self.logger.info("restoration succeed.")
                return True

    def reset_to_origin(self, feedback: bool = True):
        """
        The initialization of valve.
        """
        # different model with different feedback position.
        if "B" in self.model:
            orgin_point = 1
        elif self.model == "SV-01":
            orgin_point = 0
        else: 
            orgin_point = self.channel_num * 256 + 1
        self.send_message('reset_origin', 0)
        time.sleep(0.1)
        if feedback:
            self.feedback("motor_sts")
            if not self.feedback('current_channel', orgin_point):
                self.logger.error("restoration failed.")
                raise ValueError("restoration failed.")
            else:
                self.logger.info("restoration succeed.")
                return True
