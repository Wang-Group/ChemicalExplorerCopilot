import time
import crcmod
import logging
import serial

ADDR = {
    "initialization": 0x0100, 
    "gripper_init_sts": 0x0200, 
    "set_force": 0x0101, 
    "set_speed":0x0104, 
    "set_site": 0x0103, 
    "clamp_sts": 0x0201, 
    "set_rotation_speed": 0x0107, 
    "set_rotation_force": 0x0108, 
    "set_rotation_angle": 0x0109, 
    "rotation_sts": 0x020B, 
    }
FUNC = {
    "write": 0x06, 
    "read": 0x03
    }

def crc16add(data):
    crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
    return data + crc16(data).to_bytes(2, 'little')


class MyError(Exception):
    def __init__(self, message, code=9999):
        super().__init__(message)
        self.code = code

    def __str__(self):
        return f'{self.code}: {self.args[0]}'


class Gripper:

    """
    The Modbus communication protocol is used to control the RGI-35 series rotary electric gripper. 
    The RGI series operation manual is called to implement operations including initialization/gripper grabbing/rotation, etc.
    """
    def __init__(self, ser: serial.Serial, slave: int, _logger: logging.Logger, name: str):
        """
        :param serial_connection: COM port connection
        :param _logger: log object
        :param name: gripper name
        :param slave: Modbus slave unit ID
        """
        self.logger = _logger
        self.ser = ser
        self.slave = slave
        self.name = name

    def generate(self, func: int, addr: int, para: int):
        """
        Generate Modbus command

        Args:
            func: function code
            addr: address code
            para: parameter code
        """
        slave = self.slave.to_bytes(1, 'big')
        func = func.to_bytes(1, 'big')
        addr = addr.to_bytes(2, 'big')
        para = para.to_bytes(2, 'big')
        data = slave + func + addr + para
        command = crc16add(data)
        return command
    
    def send_message(self, func: str, addr: str, para: int) -> bytes:
        """
        send the generated message to the serial server.

        Args:
            func: function code
            addr: address code
            para: parameter code
        """
        self.ser.write(self.generate(FUNC[func], ADDR[addr], para))
        time.sleep(0.1)
        return True

    def feedback(self, 
                 addr: str, 
                 wanted: bool = None, 
                 retry: int = 10, 
                 whether_timeout: bool = False, 
                 timeout: float = 30):
        """
        The feedback of the gripper motion.

        Args:
            addr: address code
            wanted: check point. Defaults to None.
            retry: retry times. Defaults to 10.
            whether_timeout: if use the timeout. Defaults to False.
            timeout: timeout valve. Defaults to 30.
        """
        start_time = time.time()
        self.ser.readall()
        while True:
            count = 0
            while True:
                self.send_message('read', addr, 0x0001)
                receive_msg = self.ser.read_all()
                if receive_msg == b'':
                    count += 1
                else:
                    break
                if count == retry:
                    raise MyError(f'ModbusException Error, retry times: {retry}')
                time.sleep(0.1)
            if wanted:
                if receive_msg[3] * 256 + receive_msg[4] == wanted:
                    return True
            else:
                return receive_msg[3] * 256 + receive_msg[4]
            if whether_timeout:
                if time.time() - start_time >= timeout:
                    raise MyError(f'gripper {self.name} action execution timeout, over {timeout}s')
            time.sleep(0.1)

    def initialization(self, feedback_or_not: bool = True):
        """
        Initialization command.
        Args: 
            feedback_or_not: whether feedback is needed, default is True
        """
        self.logger.info(f'gripper {self.name} is initializing')
        self.send_message('write', 'initialization', 0xA5)
        if feedback_or_not:
            self.feedback('gripper_init_sts', wanted=1, whether_timeout=True)
        if "rgi" in self.name:
            self.set_rotation_angle(-90)
            self.set_site(1000)
        self.logger.info(f'gripper {self.name} initialization successful')
        return True

    def set_force(self, set_force: int = 100, feedback_or_not: bool = True):
        """
        Set the gripping force of the gripper.
        Args: 
            set_force: gripping force of the gripper (20-100, percentage)
            feedback_or_not: default True

        """
        self.send_message('write', 'set_force', set_force)
        if feedback_or_not:
            self.feedback(addr = 'set_force', wanted = set_force)
        self.logger.info(f'gripper {self.name} set_force successful, force: {set_force}')
        return True

    def set_speed(self, set_speed: int = 50, feedback_or_not: bool = True):
        """
        Set speed.
        Args: 
        set_speed: Set speed value (1-100, percentage)
        feedback_or_not: Whether to output the set speed value.
        """
        self.send_message('write', 'set_speed', set_speed)
        if feedback_or_not:
            self.feedback(addr = 'set_speed', wanted = set_speed)
        self.logger.info(f'gripper {self.name} set_speed successful, speed: {set_speed}')
        return True

    def set_site(self, set_location: int = 0, feedback_or_not: bool = True):
        """
        Set the gripper position.
        Args: 
            set_location: The gripper moves to the specified position (0-1000, thousandths)
            feedback_or_not: default False
        """
        self.send_message('write', 'set_site', set_location)
        if feedback_or_not:
            while self.feedback(addr="clamp_sts") == 0:
                time.sleep(0.1)
            clamping_state = self.feedback("clamp_sts")
            if clamping_state == 1 or clamping_state == 2:
                return True
            else:
                raise MyError(f'status of the gripper {self.name}: objects dropped')

    def set_rotation_speed(self, set_rotation_speed: int = 40, feedback_or_not: bool = True):
        """
        Set the gripper rotation speed.
        Args: 
            set_rotation_speed: rotation speed (1-100, percentage)
            feedback_or_not: default False
        """
        self.send_message('write', 'set_rotation_speed', set_rotation_speed)
        if feedback_or_not:
            self.feedback(addr='set_rotation_speed', wanted=set_rotation_speed)
        self.logger.info(f'gripper {self.name} set_rotation_speed successful, rotation_speed: {set_rotation_speed}')
        return True

    def set_rotation_force(self, set_rotation_force: int = 90, feedback_or_not: bool = True):
        """
        Set the gripper rotation force value
        Args: 
            set_rotation_force: Set the rotation force value (20-100, percentage)
            feedback_or_not: Default is False
        """
        self.send_message('write', 'set_rotation_force', set_rotation_force)
        if feedback_or_not:
            self.feedback(addr='set_rotation_force', wanted=set_rotation_force)
        self.logger.info(f'gripper {self.name} set_rotation_force successful, rotation_force: {set_rotation_force}')
        return True

    def set_rotation_angle(self, set_rotation_angle: int, feedback_or_not: bool = True):
        """
        Set the gripper rotation angle
        Args:
            set_rotation_angle: Set the rotation angle (angle range: -32768 - 32767)
            feedback_or_not: Default is True
        """

        self.send_message('write', 'set_rotation_angle', set_rotation_angle & 0xFFFF)
        if feedback_or_not:
            while self.feedback(addr="rotation_sts") == 0:
                time.sleep(0.1)
            rotation_state = self.feedback(addr="rotation_sts")
            if rotation_state == 1:
                self.logger.info(
                    f'gripper {self.name} set_rotation_angle successful, rotation_angle: {set_rotation_angle}')
                return True
            elif rotation_state == 2:
                self.logger.warning(f"the gripper is blocked, now open.")
                self.set_site(800)
            elif rotation_state == 3:
                raise MyError(f'status of gripper {self.name}: blocked and stopped')
            elif rotation_state == 0:
                self.logger.warning(f"the gripper is still rotating")
