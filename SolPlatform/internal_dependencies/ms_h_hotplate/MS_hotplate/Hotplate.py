import serial
import logging
import time 

COMMANDS = {
    "HEADER": "FE",
    "CMD_HELLO": "A0",
    "CMD_INFO": "A1",
    "CMD_STA": "A2",
    
    "CMD_SET_STIR_SPEED_RPM": "B1", # set RPM; unit: rpm, step 10 rpm
    "CMD_SET_TEMP_10x_C": "B2", # set temperature; unit: oC, step: 1 oC
    "CMD_SET_TIME_MIN": 'A5', # set timer; unit: minute, step: 1 min
    "CMD_CHG_HEAT_MOD": "B3", # set heating method; A, B, C mode

    "CMD_SW_HEAT": "B8",
    "CMD_SW_STIR": "B9",
    "CMD_SW_TIMER": "A6"}


class HotPlateController:
    def __init__(self, 
                 serial: serial.Serial, 
                 logger: logging.Logger = None
                 ) -> None:
        
        self.serial = serial
        self.logger = logger
        self.commands = COMMANDS
        self.header = self.commands["HEADER"]
        self.target_temp = None
        self.target_stir = None

        # initialize_device
        self.hello_device()
        # self.set_rpm(300)
        # self.set_temp(25)

    def add_checksum(self, byte_sequence):
        """
        Add checksum to the end of the byte sequence.
        Args:
            bytearray
        Returns:
            bytearrays with checksum
        """

        check_sum = int.to_bytes(sum(byte_sequence) % 256)
        return byte_sequence + check_sum

    def generate_send_cmd(self, method, params):
        """
        Generate send command.
        Args:
            method: command method
            params: command params
        Returns:
            bytearray with send command
        """
        hex_method = bytearray.fromhex(method)
        hex_params = int.to_bytes(params, length=2)
        hex_null_frame = int.to_bytes(0, length=1)
        add_checksum_info = self.add_checksum(hex_method + hex_params + hex_null_frame)

        send_info = bytearray.fromhex(self.header) + add_checksum_info
        return send_info

    def send_cmd(self, info):
        """
        Send command to the serial port.
        Args:
            info: bytearray with send command
        Returns:
            bytearray with feedback
        """
        # clear all the information before sending command
        self.serial.read_all()
        
        # send the command 
        self.logger.info("send:" + str(bytes(info)))
        self.serial.write(info)
        time.sleep(1)
        # read the results of the command 
        feedback = self.serial.readlines()
        # use numpy to flat the netsted list of feedback
        feedback = b"".join(feedback)
        self.logger.info("receive:" + str(feedback))
        return feedback

    def verify_feedback(self, feedback, message="hotplate feedback completed!"):
        """
        Verify feedback.
        Args:
            feedback: bytearray with feedback
        Returns:
            None
        Raises:
            ValueError: feedback error
        """

        if len(feedback) > 0 and feedback[2] == 0:
            self.logger.info(f"{message}")
        else:
            raise ValueError("hotplate command failed!")
        return

    def hello_device(self):
        """
        Send hello command to the device.
        Args:
            None
        Returns:
            None
        Raises:
            ValueError: feedback error
        """
        method = self.commands["CMD_HELLO"]
        params = 0
        info = self.generate_send_cmd(method=method, params=params)
        res = self.send_cmd(info)
        self.verify_feedback(feedback=res, message="HotPlate Connected")
        return

    def quary_info(self, content):
        """
        Send quary info command to the device.
        Args:
            content: bytearray with content
        Returns:
            None
        Raises:
            ValueError: feedback error
        """
        method = self.commands["CMD_INFO"]
        params = 0
        info = self.generate_send_cmd(method=method, params=params)
        res = list(self.send_cmd(info))
        heat_mod = res[2]
        stir_status = res[3]
        heat_status = res[4]
        timer_status = res[5]
        status = {
            "stir_status": stir_status,
            "heat_status": heat_status,
            "timer_status": timer_status,
            "heat_mod": heat_mod,
        }
        if content in status:
            return status[content]
        else:
            raise ValueError("Invalid content!")

    def quary_status(self, content):
        """
        Send quary status command to the device.
        Args:
            content: bytearray with content
        Returns:
            None
        Raises:
            ValueError: feedback error
        """

        method = self.commands["CMD_STA"]
        params = 0
        info = self.generate_send_cmd(method=method, params=params)
        res = self.send_cmd(info)
        set_rpm = int.from_bytes(res[2:4])
        actual_rpm = int.from_bytes(res[4:6])
        set_temp = int.from_bytes(res[6:8]) / 10
        actual_temp = int.from_bytes(res[8:10]) / 10
        set_timer = int.from_bytes(res[10:12])
        actual_remaining_time = int.from_bytes(res[12:14])
        status = {
            "set_rpm": set_rpm,
            "actual_rpm": actual_rpm,
            "set_temp": set_temp,
            "actual_temp": actual_temp,
            "set_timer": set_timer,
            "actual_remaining_time": actual_remaining_time,
        }
        if content in status:
            self.logger.info(f"{content}: {status[content]}")
            return status[content]
        else:
            raise ValueError("Invalid content!")

    def set_rpm(self, rpm: int = 500):
        """
        Set stir speed. the unit is rpm. 
        Args:
            rpm: stir speed (default: 500) the minimum is 100. the step size is 1.
        Returns:
            None
        Raises:
            ValueError: invalid rpm
        """
        if (rpm <= 1500) and (rpm >= 100):
            method = self.commands["CMD_SET_STIR_SPEED_RPM"]
            param = int(rpm)
            info = self.generate_send_cmd(method=method, params=param)
            self.send_cmd(info)
            self.target_stir = rpm
        else:
            raise ValueError(f"Invalid rpm! It should be between 100 and 1500 with a step size of 1. Current value is {rpm}")
        
        if self.target_temp != None:
            self.set_temp(self.target_temp)
        else:
            self.set_temp(25)

    def turn_stir_on(self):
        """
        Turn stir on.
        Returns:
            None
        """
        
        if self.quary_info("stir_status") == 1:
            method = self.commands["CMD_SW_STIR"]
            param = 0
            info = self.generate_send_cmd(method=method, params=param)
            self.send_cmd(info)
            self.logger.info("stirring is on!")
        else:
            self.logger.info("already stirring!")

        if self.target_temp != None:
            self.set_temp(self.target_temp)
        else:
            self.set_temp(25)
            
    def turn_stir_off(self):
        """
        Turn stir off.
        Returns:
            None
        """
        if self.quary_info("stir_status") == 0:
            method = self.commands["CMD_SW_STIR"]
            param = 0
            info = self.generate_send_cmd(method=method, params=param)
            self.send_cmd(info)
            self.logger.info("stirring is off!")

        else:
            self.logger.info("stirring is already off!")

        if self.target_temp != None:
            self.set_temp(self.target_temp)
        else:
            self.set_temp(25)

    def set_temp(self, temp: float = 25.0):
        """
        Set temperature. 
        Args:
            temp: temperature in Celsius. it should be between 25 and 120. 
        Returns:
            None
        """
        if (temp <= 120) and (temp>=25):
            method = self.commands["CMD_SET_TEMP_10x_C"]
            param = int(temp * 10)
            info = self.generate_send_cmd(method=method, params=param)
            self.send_cmd(info)
            self.target_temp = temp
        else:
            raise ValueError(f"Invalid temperature! It should be between 25 and 120. Current value is {temp}")

    def turn_heater_on(self):
        """
        Turn heater on.
        Returns:
            None
        """

        if self.quary_info("heat_status") == 1:
            method = self.commands["CMD_SW_HEAT"]
            param = 0
            info = self.generate_send_cmd(method=method, params=param)
            self.send_cmd(info)
            self.logger.info("heating is on!")

        else:
            self.logger.info("already heating!")

        if self.target_temp != None:
            self.set_temp(self.target_temp)
        else:
            self.set_temp(25)

    def turn_heater_off(self):
        """
        Turn heater off.
        Returns:
            None
        """
        if self.quary_info("heat_status") == 0:
            method = self.commands["CMD_SW_HEAT"]
            param = 1
            info = self.generate_send_cmd(method=method, params=param)
            self.send_cmd(info)
            self.logger.info("heating is off!")

        else:
            self.logger.info("not heating!")

        if self.target_temp != None:
            self.set_temp(self.target_temp)
        else:
            self.set_temp(25)

    def set_time(self, time: int = 0):
        """
        Set the time for the timer.
        Args:
            time (int): The time for the timer in minutes. the unit is minute. the step size is 1. Defaults to 0.
        Returns:
            None
        """
        method = self.commands["CMD_SET_TIME_MIN"]
        param = int(time)
        info = self.generate_send_cmd(method=method, params=param)
        self.send_cmd(info)
        self.logger.info(f"time has been set as {time} minutes!")

        if self.target_temp != None:
            self.set_temp(self.target_temp)
        else:
            self.set_temp(25)

    def turn_timer_on(self):
        """
        Turn timer on.
        Returns:
            None
        """

        if self.quary_info("timer_status") == 1:
            method = self.commands["CMD_SW_TIMER"]
            param = 0
            info = self.generate_send_cmd(method=method, params=param)
            self.send_cmd(info)
            self.logger.info("Timer is on!")
        else:
            self.logger.info("Timer is already on!")

        if self.target_temp != None:
            self.set_temp(self.target_temp)
        else:
            self.set_temp(25)

    def turn_timer_off(self):
        """
        Turn timer off.
        Returns:
            None
        """

        if self.quary_info("timer_status") == 0:
            method = self.commands["CMD_SW_TIMER"]
            param = 1
            info = self.generate_send_cmd(method=method, params=param)
            self.send_cmd(info)
            self.logger.info("Timer is off!")
        else:
            self.logger.info("Timer is already off!")
            
        if self.target_temp != None:
            self.set_temp(self.target_temp)
        else:
            self.set_temp(25)