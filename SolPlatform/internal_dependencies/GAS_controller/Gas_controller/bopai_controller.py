from .GAS_AT_Command import ATCommand
from typing import Dict
import time
import serial
import logging
import threading

class thread_safe_serial(serial.Serial):
    def __init__(self):
        self.lock = threading.Lock()

    def thread_safe_write(self, content):
        self.lock.acquire()
        self.write(content)
        self.lock.release()
        
class GASAxis(ATCommand):
    def __init__(self, motion_prm: Dict[str, dict], logger: logging.Logger):
        super().__init__(serial.Serial(**motion_prm['connection_param']))
        self.logger = logger
        # initialize the param of controller
        self.op = motion_prm['op']
        self.ip = motion_prm['ip']
        self.dac = motion_prm['dac']
        self.adc = motion_prm['adc']
        self.axis = motion_prm['axis']
        self.safe_coordinate = motion_prm['safe_coordiniate']
        self.trap_param = motion_prm['trap_param']
        self.jog_param = motion_prm['jog_param']
        self.home_param = motion_prm['home_param']
        # initialize the position of motor
        self.position = {}
        # initialize the motion param
        self.motor_param = motion_prm['motor_param']
        self.pls_per_mm = {}
        for key, value in self.motor_param.items():
            self.pls_per_mm[key] = int(value[0] / value[1])
        self.format_trap_param()
        self.format_jog_param()
        self.format_home_param()
        # initialzize the limits
        # self.set_limitP()
        # self.set_limitN()
        
    def connection(self):
        """
        connect with the card on the rs232 link.
        """
        ret = self.GA_Open()
        if ret == b'AT+Error':
            raise ConnectionError("failed to connect with bopai controller")
        ret = self.GA_Reset()
        if ret == b'AT+Error':
            raise RuntimeError("failed to reset the bopai controller")
        for axis_index, axis_num in self.axis.items():
            ret = self.GA_AxisOn(axis_num)
            if ret == b'AT+Error':
                raise RuntimeError(f"axis {axis_index} mission 'ENABLE' failed")

    def disconnection(self):
        """
        disconnect with the card.

        """
        for axis_index, axis_num in self.axis.items():
            ret = self.GA_AxisOff(axis_num)
            if ret == b'AT+Error':
                raise RuntimeError(f"axis {axis_index} mission 'DISABLE' failed")
        ret = self.GA_Close()
        if ret == b'AT+Error':
            raise ConnectionError("failed to disconnect with bopai controller")

    def format_trap_param(self): 
        """
        Format the trap param.
        """
        # mm/s -> pulse/ms; mm/s/s -> pulse/ms/ms; s -> ms
        for key, value in self.trap_param.items():
            # dAcc
            self.trap_param[key][0] = round(value[0] * self.pls_per_mm[key] / 1000 / 1000, 3)
            # dDec
            self.trap_param[key][1] = round(value[1] * self.pls_per_mm[key] / 1000 / 1000, 3)
            # dSmoothTime
            self.trap_param[key][2] = int(value[2] * 1000)
            # dVelStart
            self.trap_param[key][3] = round(value[3] * self.pls_per_mm[key] / 1000, 3)

    def format_jog_param(self): 
        """
        Format the jog param.
        """
        # mm/s -> pulse/ms; mm/s/s -> pulse/ms/ms; s -> ms
        for key, value in self.jog_param.items():
            # dAcc
            self.jog_param[key][0] = round(value[0] * self.pls_per_mm[key] / 1000 / 1000, 3)
            # dDec
            self.jog_param[key][1] = round(value[1] * self.pls_per_mm[key] / 1000 / 1000, 3)
            # dSmoothTime
            self.jog_param[key][2] = int(value[2] * 1000)

    def format_home_param(self): 
        """
        Format the home param.
        """
        # mm/s -> pulse/ms; mm/s/s -> pulse/ms/ms; s -> ms
        for key, value in self.home_param.items():
            # dHomeRapidVel
            self.home_param[key][3] = round(value[3] * self.pls_per_mm[key] / 1000, 3)
            # dHomeLocatVel
            self.home_param[key][4] = round(value[4] * self.pls_per_mm[key] / 1000, 3)
            # dHomeIndexVel
            self.home_param[key][5] = round(value[5] * self.pls_per_mm[key] / 1000, 3)
            # dHomeAcc
            self.home_param[key][6] = round(value[6] * self.pls_per_mm[key] / 1000 / 1000, 3)
    
    def set_limitP(self): 
        """
        Set the positive limit.

        """
        for key, value in self.ip.items():
            ret = self.GA_LmtsOn(key, 0)
            if ret == b'AT+Error':
                raise RuntimeError(f"axis {key} mission 'GA_LmtsOn' failed")
            if value[1] != -1:
                ret = self.GA_SetHardLimP(key, value[1])
                if ret == b'AT+Error':
                    raise RuntimeError(f"axis {key} mission 'GA_SetHardLimP' failed")

    def set_limitN(self): 
        """
        Set the nagative limit.

        """
        for key, value in self.ip.items():
            ret = self.GA_LmtsOn(key, 0)
            if ret == b'AT+Error':
                raise RuntimeError(f"axis {key} mission 'GA_LmtsOn' failed")
            if value[1] != -1:
                ret = self.GA_SetHardLimN(key, value[1])
                if ret == b'AT+Error':
                    raise RuntimeError(f"axis {key} mission 'GA_SetHardLimN' failed")

    def to_LimitN(self, axis_index: str, vel: float, feedback: bool = True):
        axis_number = self.axis[axis_index]
        ret = self.GA_LmtsOn(axis_number, 1)
        if ret == b'AT+Error':
            raise RuntimeError(f"axis {axis_index} mission 'GA_LmtsOn' failed")
        if self.ip[axis_number][0] != -1:
            ret = self.GA_SetHardLimN(axis_number, self.ip[axis_number][0])
            if ret == b'AT+Error':
                raise RuntimeError(f"axis {axis_index} mission 'GA_SetHardLimN' failed")
        else:
            raise ValueError
        self.jog(axis_index=axis_index, vel=vel, feedback=feedback)
        ret = self.GA_LmtsOff(axis_number, 1)

        if ret == b'AT+Error':
            raise RuntimeError(f"axis {axis_index} mission 'GA_LmtsOff' failed")

    def return_home(self, axis_index: str, feedback: bool = True, home_start: bool = True, to_LimitN: bool = False, to_LimitN_vel: float = None):
        """
        return to the zero point and record the coordinate of zero point.

        Args:
            axis_index: the name of axis
            feedback: choice of feedback. Defaults to True.
            home_start: whether the axis returning home or not. Defaults to True.
            to_LimitN: _description_. Defaults to False.
            to_LimitN_vel: _description_. Defaults to None.

        """
        axis_number = self.axis[axis_index]
        if to_LimitN:
            self.to_LimitN(axis_index=axis_index, vel=to_LimitN_vel, feedback=True)
        ret = self.GA_HomeSetPrmSingle(axis_number, *self.home_param[axis_number])
        if ret == b'AT+Error':
            raise RuntimeError(f"axis {axis_index} mission 'GA_HomeSetPrmSingle' failed")
        self.position[axis_index] = 0
        if home_start:
            ret = self.GA_HomeStart(axis_number)
            if ret == b'AT+Error':
                raise RuntimeError(f"axis {axis_index} mission 'GA_HomeStart' failed")
            if feedback:
                while True:
                    ret = self.GA_HomeGetSts(axis_number)
                    if ret == b'AT+Error':
                        raise RuntimeError(f"axis {axis_index} mission 'GA_HomeGetSts' failed")
                    elif int(ret.decode().split('+')[2]) == 2:
                        break
                    time.sleep(0.1)
        
    
    def datum_xyz(self):
        """
        three axis return home.
        """
        self.return_home("z")
        self.return_home("x", home_start = False)
        self.return_home("y", home_start = False)
        xy_dict = {}
        xy_dict['x'] = self.axis['x']
        xy_dict['y'] = self.axis['y']
        x = threading.Thread(target = self.GA_HomeStart, args = (xy_dict['x'], ))
        y = threading.Thread(target = self.GA_HomeStart, args = (xy_dict['y'], ))
        x.start()
        y.start()
        x.join()
        y.join()
        for axis_index, axis_number in xy_dict.items():
            while True:
                ret = self.GA_HomeGetSts(axis_number)
                if ret == b'AT+Error':
                    raise RuntimeError(f"axis {axis_index} mission 'GA_HomeGetSts' failed")
                elif int(ret.decode().split('+')[2]) == 2:
                    break
                time.sleep(0.1)

    def stop(self, *axis_index: str):
        """
        stop all axis.
        """
        axis_list = []
        for axis in axis_index:
            axis_list.append(self.axis[axis])
        self.GA_Stop(*axis_list)

    def jog(self, axis_index: str, vel: int, GA_Update: bool = True, feedback: bool = False):
        """
        move axis by the set speed.

        Args:
            axis_index: the name of axis
            vel: the speed of axis, if wanted to stop, just make it 0, unit: rpm.
            GA_Update: whether the axis moving or not. Defaults to True.
            feedback: choice of feedback. Defaults to False.
        """
        axis_number = self.axis[axis_index]
        ret = self.GA_PrfJog(axis_number)
        if ret == b'AT+Error':
            raise RuntimeError(f"axis {axis_index} mission 'GA_PrfJog' failed")
        ret = self.GA_SetJogPrm(axis_number, *self.jog_param[axis_number])
        if ret == b'AT+Error':
            raise RuntimeError(f"axis {axis_index} mission 'GA_SetJogPrm' failed")
        ret = self.GA_SetVel(axis_number, round(vel * self.pls_per_mm[axis_number] / 1000, 1))
        if ret == b'AT+Error':
            raise RuntimeError(f"axis {axis_index} mission 'GA_SetVel' failed")
        if GA_Update:
            ret = self.GA_Update(axis_number)
            if ret == b'AT+Error':
                raise RuntimeError(f"axis {axis_index} mission 'GA_Update' failed")
            if feedback:
                while True:
                    ret = self.GA_GetSts(axis_number)
                    if ret == b'AT+Error':
                        raise RuntimeError(f"axis {axis_index} mission 'GA_GetSts' failed")
                    elif int(ret.decode().split('+')[2]) == 2624:
                        return True, 'negative'
                    time.sleep(0.1)

    def trap(self, axis_index: str, pos: float, vel: float = 100, GA_Update: bool = True, feedback: bool = True):
        """
        move single axis to a selected point.

        Args:
            axis_index: the axis name, refers to config file.
            pos: the distance axis will move.
            vel: the speed of the axis. Defaults to 100.
            GA_Update: whether the axis moving or not. Defaults to True.
            feedback: choice of feedback. Defaults to True.
        """
        axis_number = self.axis[axis_index]
        ret = self.GA_PrfTrap(axis_number)
        if ret == b'AT+Error':
            raise RuntimeError(f"axis {axis_index} mission 'GA_PrfJog' failed")
        ret = self.GA_SetTrapPrm(axis_number, *self.trap_param[axis_number])
        if ret == b'AT+Error':
            raise RuntimeError(f"axis {axis_index} mission 'GA_SetTrapPrmSingle' failed")
        ret = self.GA_SetPos(axis_number, int(pos * self.pls_per_mm[axis_number]))
        if ret == b'AT+Error':
            raise RuntimeError(f"axis {axis_index} mission 'GA_SetPos' failed")
        ret = self.GA_SetVel(axis_number, round(vel * self.pls_per_mm[axis_number] / 1000, 1))
        if ret == b'AT+Error':
            raise RuntimeError(f"axis {axis_index} mission 'GA_SetVel' failed")
        self.position[axis_index] = pos
        if GA_Update:
            ret = self.GA_Update(axis_number)
            if ret == b'AT+Error':
                raise RuntimeError(f"axis {axis_index} mission 'GA_Update' failed")
            if feedback:
                while True:
                    ret = self.GA_GetSts(axis_number)
                    if ret == b'AT+Error':
                        raise RuntimeError(f"axis {axis_index} mission 'GA_GetSts' failed")
                    # ret = "AT+GetSts+AXIS_STATUS"
                    elif (int(ret.decode().split('+')[2]) == 10752) or (int(ret.decode().split('+')[2]) == 27136) or (int(ret.decode().split('+')[2]) == 2560):
                        self.position[axis_index] = pos
                        return True
                    elif int(ret.decode().split('+')[2]) == 10784:
                        raise RuntimeError(f"axis {axis_index}'s positive hard limit triggered")
                    elif int(ret.decode().split('+')[2]) == 10816:
                        raise RuntimeError(f"axis {axis_index}'s negative hard limit triggered")
                    time.sleep(0.1)

    def move_xyz(self, position: list, speed: list = [100, 100, 50]):
        """
        move triple_axis to a point in the space

        Args:
            position: the coordinate of the point, list, e.g. [x, y, z]
            speed: the speed of these axis. Defaults to [100, 100, 100].

        """
        if self.position["x"] != position[0] or self.position["y"] != position[1]:
            self.trap("z", self.safe_coordinate["z"], speed[2])
        self.trap("x", position[0], speed[0], GA_Update = False)
        self.trap("y", position[1], speed[1], GA_Update = False)
        self.GA_Update()
        xy_dict = {}
        xy_dict['x'] = self.axis['x']
        xy_dict['y'] = self.axis['y']
        for axis_index, axis_number in xy_dict.items():
            while True:
                ret = self.GA_GetSts(axis_number)
                if ret == b'AT+Error':
                    raise RuntimeError(f"axis {axis_index} mission 'GA_GetSts' failed")
                # ret = "AT+GetSts+AXIS_STATUS"
                elif (int(ret.decode().split('+')[2]) == 10752) or (int(ret.decode().split('+')[2]) == 27136):
                    # self.position[axis_index] =  position[axis_number - 1]
                    break
                elif int(ret.decode().split('+')[2]) == 10784:
                    raise RuntimeError(f"axis {axis_index}'s positive hard limit triggered")
                elif int(ret.decode().split('+')[2]) == 10816:
                    raise RuntimeError(f"axis {axis_index}'s negative hard limit triggered")
                time.sleep(0.1)
        self.trap("z", position[2], speed[2])

    def rotate(self, axis_index: str, degree: float, vel: float, GA_Update: bool = True, feedback: bool = True):
        self.trap(axis_index=axis_index, 
                  pos=(self.position[axis_index] + degree) / 360, 
                  vel=vel, 
                  GA_Update=False, 
                  feedback=False
                  )
        axis_number = self.axis[axis_index]
        if GA_Update:
            ret = self.GA_Update(axis_number)
            if ret == b'AT+Error':
                raise RuntimeError(f"axis {axis_index} mission 'GA_Update' failed")
            if feedback:
                while True:
                    ret = self.GA_GetSts(axis_number)
                    if ret == b'AT+Error':
                        raise RuntimeError(f"axis {axis_index} mission 'GA_GetSts' failed")
                    elif int(ret.decode().split('+')[2]) == (10752 or 27136):
                        self.position[axis_index] = (self.position[axis_index] + degree) % 360
                        if self.position[axis_index] == 0:
                            self.GA_ZeroPos(axis_number)
                        return True
                    
    def analog_trigger(self, dac_index: str, voltage: float):
        """
        set the analog voltage

        Args:
            dac_index: the analog index
            voltage: the voltage, 0-10 V
        """

        ret = self.GA_SetDac(self.dac[dac_index], voltage)
        if ret == 'AT+Error':
            raise RuntimeError(f"dac {dac_index} mission 'GA_SetDac' failed")
        
    def read_analog(self, adc_index: str): 
        """
        read the analog, unit: V

        Args:
            adc_index: the analog index 
        """
        ret = self.GA_GetAdc(self.adc[adc_index])
        if ret == 'AT+Error':
            raise RuntimeError(f"dac {adc_index} mission 'GA_GetAdc' failed")
        adc = int((ret.decode().split("+")[2])) / 1000
        return adc

    def output_trigger(self, op_index: str, onoff: bool):
        """
        turn the selected output on or off

        Args:
            op_index: the index of output
            onoff: turn the output on or off
        """
        if onoff:
            ret = self.GA_SetExtDoBit(self.op[op_index], 1)
            if ret == 'AT+Error':
                raise RuntimeError(f"op {op_index} mission 'GA_SetExtDoBit' failed")
        else: 
            ret = self.GA_SetExtDoBit(self.op[op_index], 0)
            if ret == 'AT+Error':
                raise RuntimeError(f"op {op_index} mission 'GA_SetExtDoBit' failed")
