import time
import serial
import logging
from .runze_commands import COMMANDS


class BaseDevice:
    """
    The base operations of runze devices.
    """
    def __init__(self, ser: serial.Serial, slave: int, logger: logging.Logger):
        """
        initialize the commands of devices

        Args:
            ser: serial connection
            slave: the device number
            logger: logger
        """
        # define the commands
        self.basic_commands = COMMANDS
        self.commands = {}
        self.Common_commands = {}
        self.SwitchValve_commands = {}
        self.SyringePump_commands = {}
        self.PeristalticPump_commands = {}
        self.Common_commands = self.basic_commands["Common_commands"]
        self.SwitchValve_commands = self.basic_commands["SwitchValve_commands"]
        self.SyringePump_commands = self.basic_commands["SyringePump_commands"]
        self.Injector_commands = self.basic_commands["Injector_commands"]
        self.PeristalticPump_commands = self.basic_commands["PeristalticPump_commands"]
        # initialize the connections
        self.logger = logger
        self.ser = ser
        self.slave = slave

    def set_commands_dict(self, installation: str = 'SwitchValve' or 'SyringePump' or 'Injector' or 'PeristalticPump'):
        """
        set the commands dict of different kinds of device.

        Args:
            installation: the type of device. Defaults to 'SwitchValve'or'SyringePump'or'Injector'or'PeristalticPump'.
        """
        if installation == 'SwitchValve':
            self.commands = {**self.Common_commands, **self.SwitchValve_commands}
        elif installation == 'SyringePump':
            self.commands = {**self.Common_commands, **self.SyringePump_commands}
        elif installation == 'Injector':
            self.commands = {**self.Common_commands, **self.Injector_commands}
        elif installation == "PeristalticPump":
            self.commands = {**self.Common_commands, **self.PeristalticPump_commands}

    def generate(self, func: str, para: int) -> bytes:
        """
        Generate the message before being sent to serial port.

        Args:
            func: the function of device
            para: the param of device

        Returns:
            generated message
        """
        STX = self.commands["STX"].to_bytes(1, "big")
        ETX = self.commands["ETX"].to_bytes(1, "big")
        FUNC = self.commands[func].to_bytes(1, 'big')
        ADDR = self.slave.to_bytes(1, 'big')
        PARA = para.to_bytes(2, 'little')
        CHECKSUM = (STX[0] + ETX[0] + ADDR[0] + FUNC[0] + PARA[0] + PARA[1]).to_bytes(2, 'little')
        return STX + ADDR + FUNC + PARA + ETX + CHECKSUM

    def send_message(self, func: str, para: int, timeout: int = 5) -> bytes:
        """
        send the generated message to serial port.

        Args:
            func: the name of device func
            para: the param of device func
            timeout: sending message timeout. Defaults to 5.
        """
        start_time = time.time()
        self.ser.read_all()
        self.ser.write(self.generate(func, para))
        while True:
            time.sleep(0.1)
            receive_message = self.ser.read_all()
            if receive_message != b'':
                break
            self.ser.write(self.generate(func, para))
            if time.time() - start_time >= timeout:
                raise TimeoutError(f"feedback timeout, message: {self.generate(func, para).hex(sep= ' ').upper()}")
        return receive_message


    def feedback(self, func: str, wanted: int = None, timeout: int = 60*1):
        """
        feedback of motor, or other function.

        Args:
            func: the name of func
            wanted: value to compare with feedback value. Defaults to None.
            timeout: the time out of function. Defaults to 60*1.
        """
        start_time = time.time()
        while True:
            feedback_value = self.send_message(func, 0)
            if func == "motor_sts" and feedback_value[2] == wanted:
                return True
            elif func == "motor_sts" and feedback_value[2] != wanted and wanted != None:
                return False
            if feedback_value[2] == 0:
                if wanted is not None:
                    if feedback_value[3] + feedback_value[4] * 256 <= wanted + 1 and feedback_value[3] + feedback_value[4] * 256 >= wanted - 1:
                        return True
                    else:
                        return False
                else:
                    return feedback_value[3] + feedback_value[4] * 256
            
            if time.time() - start_time >= timeout:
                raise TimeoutError(f'feedback timeout, error code: {hex(feedback_value[2])}')
            time.sleep(0.1)


    def valve_switch(self, param: dict, channel: str, feedback=True):
        """
        Switch the valve to the wanted channel.

        Args:
            param: the dict of channel.
            channel: the name of channel.
            feedback: feedback trigger. Defaults to True.

        """
        self.send_message('valve_switch', param[channel])
        if feedback:
            self.feedback("motor_sts")
            current_valve = self.feedback('current_channel')
            if not self.feedback('current_channel', param[channel]):
                self.logger.error(f"valve swtich failed, current valve is {current_valve}.")
                raise ValueError(f"valve swtich failed, current valve is {current_valve}.")
            else:
                self.logger.info(f'current channel: {param[channel]}')

    def forced_to_stop(self):
        """
        Force to stop device.
        """
        self.send_message('forced_stop', 0)

    def close(self):
        """
        close the serial port.
        """
        self.ser.close()
        self.logger.info('COM is closed.')
