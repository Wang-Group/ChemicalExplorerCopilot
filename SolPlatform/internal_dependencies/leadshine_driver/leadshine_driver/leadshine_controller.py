import time
import crcmod
import logging
import serial
from typing import Union, Optional
from .leadshine_addr import*

def crc16(data):
    crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
    crcode = crc16(data).to_bytes(2, 'little')
    return crcode

class LeadShine_Controller:
    """
    The control class of Leadshine driver: DM2C serials and CL2C serials.
    """

    def __init__(self, ser: serial.Serial, slave: int, motion_param: dict , logger: logging.Logger) -> None:
        # initialize serial
        self.ser = ser
        self.slave = slave
        # initialize the param of motor
        self.motion_param = motion_param
        self.logger = logger
        self.datum_param = self.motion_param["datum_param"]
        self.moving_param = self.motion_param["moving_param"]
        self.ip = self.motion_param["ip"]
        self.op = self.motion_param["op"]
        # calculate the pulse need to send per mm
        self.send_message("Pr0.00", self.motion_param["pulse_circle"])
        self.send_message("Pr5.00", self.motion_param["peak_current"])
        # set the origin point input
        self.send_message(self.ip["datum_in"], 0x27)
        self.send_message("control_board", 0x2244)
        self.pulse_mm = int(self.motion_param["pulse_circle"] / self.motion_param["pitch_of_screws"])
        self.set_datum_param()
        self.set_moving_param()
        self.current_position = None


    def generate(self, func: int, addr: int, param: int):
        """
        Generate the message before send to serial.

        Args:
            func: the read/write mode. {"read": 0x03, "write": 0x06 }
            addr: the addr of modbus coil for different functions
            param: the param of function

        Returns:
            generated message.
        """
        slave = self.slave.to_bytes(1, 'big')
        func = func.to_bytes(1, 'big')
        addr = addr.to_bytes(2, 'big')
        param = param.to_bytes(2, 'big')
        data = slave + func + addr + param
        command = data + crc16(data)
        return command
    
    def send_message(self, addr: str, param: int = 0x0000, timeout: int = 5) -> bytes:
        """
        send message to the serial port.

        Args:
            addr: the name of function address
            param: param. Defaults to 0x0000.
            timeout: the timeout of sending message. Defaults to 5.
        """
        start_time = time.time()
        self.ser.read_all()
        if addr in READ_ADDR.keys():
            addr = READ_ADDR[addr]
            func = 0x03
            receive_num = self.ser.write(self.generate(func, addr, param))
        elif addr in WRITE_ADDR.keys():
            addr = WRITE_ADDR[addr]
            func = 0x06
            receive_num = self.ser.write(self.generate(func, addr, param))
        else: 
            raise ValueError(f"addr should be in the dict, current value is {addr}")
        while True:
            time.sleep(0.1)
            receive_message = self.ser.read_all()
            if receive_num:
                break
            receive_num = self.ser.write(self.generate(func, addr, param))
            if time.time() - start_time >= timeout:
                raise TimeoutError(f"feedback timeout, message: {self.generate(func, addr, param).hex(sep= ' ').upper()}")
        return receive_message
    
    def feedback(self, wanted: Optional[int] = None, timeout: int = 20):
        """
        get the feedback of motor motion or other function.

        Args:
            wanted: the param compare to the feedback valve. Defaults to None.
            timeout: feedback timeout. Defaults to 20 s.
        """
        start_time = time.time()
        while True:
            feedback_value = self.send_message("motion_status", 1)
            feedback_num = 0
            for i in range(3, feedback_value[2] + 3):
                feedback_num += feedback_value[i]
            if feedback_num == 0:
                if wanted is not None:
                    if wanted == feedback_num:
                        return True
                    else:
                        print(f"error code is {feedback_num}")
                        return False
                else:
                    return feedback_num
            time.sleep(0.1)

    def set_brk(self, brk_index: str): 
        """
        set the brk ouput

        Args:
            brk_index: the name of brk output.
        """
        self.send_message(self.op[brk_index], 0x0024)

    def set_moving_param(self): 
        """
        set the accelerate time, decelerate time, and defualt speed.
        """
        # set acc time
        self.send_message("Pr9.04", int(self.moving_param[0]))
        # set dec time
        self.send_message("Pr9.05", int(self.moving_param[1]))
        # set defualt speed
        self.send_message("Pr9.03", int(60 * self.moving_param[2] / self.motion_param["pitch_of_screws"]))
        # save to EEPROM
        # self.send_message("control_board", 0x2244)

    def set_datum_param(self):
        """
        set the datum param from config file.
        """
        # set home mode
        # self.send_message("Pr8.10", self.datum_param[0])
        # set datum high speed
        self.send_message("Pr8.15", int(60 * self.datum_param[0] / self.motion_param["pitch_of_screws"]))
        # set datum low speed
        self.send_message("Pr8.16", int(60 * self.datum_param[1] / self.motion_param["pitch_of_screws"]))
        # set datum acc time
        self.send_message("Pr8.17", int(self.datum_param[2]))
        # set datum dec time
        self.send_message("Pr8.18", int(self.datum_param[3]))
        # save to EEPROM
        # self.send_message("control_board", 0x2244)

    def set_position(self, pos: float):
        """
        set the target position, unit: mm/degree

        Args:
            pos: the position
        """
        # calculate how much pulse(step) is needed
        step = int(self.pulse_mm * pos)
        # transfer the step into hex
        hex_to_transer = "%08x" % step
        # bytes_to_send = bytes.fromhex(hex_to_transer)
        high = int(hex_to_transer[0:4], 16)
        low = int(hex_to_transer[4:], 16)
        # send the high and low position
        self.send_message("Pr9.01", high)
        self.send_message("Pr9.02", low)
        # save to EEPROM
        # self.send_message("control_board", 0x2244)

    def datum(self, feedback: bool = True):
        """
        axis return home

        Args:
            feedback: feedback trigger. Defaults to True.
        """
        self.send_message("Pr0.03", 0)
        self.send_message("control_board", 0x2244)
        self.send_message("Pr8.10", self.datum_param[4])
        self.send_message("Pr8.02", 0x020)
        if feedback:
            self.feedback(0)
        self.send_message("Pr8.02", 0x21)
        self.current_position = 0

    def absolute_move(self, pos: float, speed: Optional[float] = None, feedback: bool = True):
        """
        motor absolute to target position from home position.

        Args:
            pos: abs position
            speed: moving speed. Defaults to None.
            feedback: feedback trigger. Defaults to True.
        """
        self.send_message("Pr9.00", 0x0001)
        if speed: 
            self.send_message("Pr9.03", int(60 * speed / self.motion_param["pitch_of_screws"]))
        if pos < 0:
            self.send_message("Pr0.03", 1)
        else: 
            self.send_message("Pr0.03", 0)
        self.send_message("control_board", 0x2244)
        # set the position
        self.set_position(abs(pos))
        # start motion
        self.send_message("Pr8.02", 0X0010)
        # feedback if needed
        if feedback:
            self.feedback(0)
            self.current_position = pos
        # self.send_message("Pr9.00", 0)
    
    def relative_move(self, pos: float, speed: Optional[float] = None, feedback: bool = True):
        """
        motor relative move to target position from current position.

        Args:
            pos: rel position
            speed: moving speed. Defaults to None.
            feedback: feedback trigger. Defaults to True.
        """
        self.send_message("Pr9.00", 0x0041)
        if speed: 
            self.send_message("Pr9.03", int(60 * speed / self.motion_param["pitch_of_screws"]))
        if pos < 0:
            self.send_message("Pr0.03", 1)
        else: 
            self.send_message("Pr0.03", 0)
        self.send_message("control_board", 0x2244)
        # set the position
        self.set_position(abs(pos))
        # start motion
        self.send_message("Pr8.02", 0X0010)
        # feedback if needed
        if feedback:
            self.feedback(0)
            self.current_position += pos
        # self.send_message("Pr9.00", 0)

    def jog(self, speed: int): 
        """
        motor move in jog mode.

        Args:
            speed: the speed of jog, unit: rpm. when speed is 0, stop.
        """
        if speed: 
            # set the jog mode
            self.send_message("Pr9.00", 0x0002)
            # set the speed
            self.send_message("Pr9.03", speed)
            # start motion
            self.send_message("Pr8.02", 0X0010)
        else:
            # stop the jog
            self.send_message("Pr8.02", 0X0040)
    
    def output_trigger(self, index: str, onoff: bool): 
        """
        turn on the output or not.

        Args:
            index: the name of output
            onoff: the trigger
        """
        if onoff: 
            self.send_message(self.op[index], 0x0080)
        else:
            self.send_message(self.op[index], 0)
