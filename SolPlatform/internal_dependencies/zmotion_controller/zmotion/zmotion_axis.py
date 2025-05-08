from .zauxdllPython import *
from typing import Optional
import time
import threading
import logging


flag_lock = threading.Lock()


class AxisMotion:
    def __init__(self, motion_prm: dict, logger: logging.Logger):
        # Check if all necessary keys are in motion_prm
        required_keys = ['ipaddr', 'axis', 'op', 'ip', 'param', 'default_safe_coordinates']
        for key in required_keys:
            if key not in motion_prm:
                raise ValueError(f'motion_prm is missing key: {key}')
        self.logger = logger
        # initialize the param of the controller
        self.zaux = ZAUXDLL()
        self.ipaddr = motion_prm['ipaddr']
        self.axis = motion_prm['axis']
        self.op = motion_prm['op']
        self.ip = motion_prm['ip']
        self.param = motion_prm['param']
        self.default_safe_coordinates = motion_prm['default_safe_coordinates']
        self.max_motion_range = motion_prm['max_motion_range']
        # init
        self.connect()
        self._set_param()
        # init multi-axis motion flag
        self.flag = 0

    def connect(self):
        # CONNECTION
        ret = self.zaux.ZAux_OpenEth(self.ipaddr)
        if ret != 0:
            raise ConnectionError('ethernet connection to controller failed', ret)
        self.logger.info("successful connection to the controller")
        # ENABLE
        for axis_index, axis_num in self.axis.items():
            ret = self.zaux.ZAux_Direct_SetOp(self.op[axis_num][0], 1)
            if ret != 0:
                raise RuntimeError(f"axis {axis_index} mission 'ENABLE' failed", ret)
        self.logger.info("output port enable successful")
        return True

    def disconnect(self):
        # DISABLE
        for axis_index, axis_num in self.axis.items():
            ret = self.zaux.ZAux_Direct_SetOp(self.op[axis_num][0], 0)
            if ret != 0:
                raise RuntimeError(f"axis {axis_index} mission 'DISABLE' failed", ret)
        # Add check_command method or remove this line if not needed
        ret = self.zaux.ZAux_Close()
        if ret:
            raise RuntimeError(f"mission 'Close' failed, error code{ret}")
        self.logger.info("successful disconnection to the controller")

    def _set_param(self):
        """
        set the default parameters, which are recorded in the config file
        Returns:

        """
        # SET MOVING PARAMETER
        for axis_index, axis_num in self.axis.items():
            ret = 0
            ret += self.zaux.ZAux_Direct_SetAtype(axis_num, self.param[axis_num][0])
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Set_Atype' failed, error code{ret}")
            ret += self.zaux.ZAux_Direct_SetInvertStep(axis_num, self.param[axis_num][1])
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Set_Invert_Step' failed, error code{ret}")
            ret += self.zaux.ZAux_Direct_SetUnits(axis_num, self.param[axis_num][2])
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Set_Units' failed, error code{ret}")
            ret += self.zaux.ZAux_Direct_SetAccel(axis_num, self.param[axis_num][3])
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Set_Accel' failed, error code{ret}")
            ret += self.zaux.ZAux_Direct_SetDecel(axis_num, self.param[axis_num][4])
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Set_Decel' failed, error code{ret}")
            ret += self.zaux.ZAux_Direct_SetFastDec(axis_num, self.param[axis_num][5])
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Set_FastDec' failed, error code{ret}")
            ret += self.zaux.ZAux_Direct_SetSpeed(axis_num, self.param[axis_num][6])
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Set_Speed' failed, error code{ret}")
            ret += self.zaux.ZAux_Direct_SetSramp(axis_num, self.param[axis_num][7])
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Set_Sramp' failed, error code{ret}")
            ret += self.zaux.ZAux_Direct_SetCreep(axis_num, self.param[axis_num][8])
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Set_Creep' failed, error code{ret}")
        # SET INPUT SIGNAL
        for axis_index, axis_num in self.axis.items():
            ret = 0
            ret += self.zaux.ZAux_Direct_SetDatumIn(axis_num, self.ip[axis_num][0])
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Set_Datum_In' failed, error code{ret}")
            ret += self.zaux.ZAux_Direct_SetInvertIn(self.ip[axis_num][0], 1)
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Set_Invert_In' failed, error code{ret}")
            ret += self.zaux.ZAux_Direct_SetFwdIn(axis_num, self.ip[axis_num][1])
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Set_Fwd_In' failed, error code{ret}")
            ret += self.zaux.ZAux_Direct_SetRevIn(axis_num, self.ip[axis_num][2])
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Set_Rev_In' failed, error code{ret}")
            ret += self.zaux.ZAux_Direct_SetAlmIn(axis_num, self.ip[axis_num][3])
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Set_Alm_In' failed, error code{ret}")
        self.logger.info("setting parameters succeed")
        return True

    def datum(self, axis_index: str) -> bool:
        """
        single-axis return home
        Args:
            axis_index: indicate which axis to return home

        Returns: True, if this function is executed successfully, otherwise, raise RuntimeError

        """
        axis_num = self.axis[axis_index]
        flag_lock.acquire()
        if self.flag == 0:
            flag_lock.release()
            if self.axis_status(axis_index) == 0:
                param = self.param[axis_num]
                self.set_speed(axis_index, param[10])
                ret = 0
                ret += self.zaux.ZAux_Direct_Single_Datum(axis_num, param[9])
                if ret:
                    flag_lock.acquire()
                    self.flag += 1
                    flag_lock.release()
                    raise RuntimeError(f"axis {axis_index} mission 'Single_Datum' failed, error code{ret}")
                while True:
                    ret, val = self.zaux.ZAux_Direct_GetHomeStatus(axis_num)
                    if ret:
                        flag_lock.acquire()
                        self.flag += 1
                        flag_lock.release()
                        raise RuntimeError(f"axis {axis_index} mission 'Get_Home_Status' failed, error code{ret}")
                    if val:
                        break
                    time.sleep(0.1)
                ret += self.zaux.ZAux_Direct_SetMpos(axis_num, 0.000)
                if ret:
                    raise RuntimeError(f"axis {axis_index} mission 'Set_Mpos' failed, error code{ret}")
                self.set_speed(axis_index, param[6])
                self.logger.info(f"axis {axis_index} return home successful")
                return True
            else:
                flag_lock.acquire()
                self.flag += 1
                flag_lock.release()
                raise RuntimeError(f"axis {axis_index} error occurred, error code: {self.axis_status(axis_index)}")
        else:
            flag_lock.release()
            raise RuntimeError(f"some errors occurred in other axes, current axis: {axis_index}")

    def datum_xyz(self):
        """
        all axis return home
        Operation_Logic:
            axis z1 & z2 return home first, then move axis x & y

        Returns: True, if this function is executed successfully

        """
        x = threading.Thread(target=self.datum, args=('x',))
        y = threading.Thread(target=self.datum, args=('y',))
        z1 = threading.Thread(target=self.datum, args=('z1',))
        z2 = threading.Thread(target=self.datum, args=('z2',))
        z1.start()
        z2.start()
        z1.join()
        z2.join()
        x.start()
        y.start()
        x.join()
        y.join()
        self.logger.info('all axes return home successful')
        return True

    def set_speed(self, axis_index: str, speed: int) -> bool:
        """
        set the speed of a specific axis
        Args:
            axis_index: the axis to execute this function
            speed: unit is mm/s

        Returns: True, if this function is executed successfully, otherwise, raise RuntimeError or ValueError

        """
        axis_num = self.axis[axis_index]
        ret = self.zaux.ZAux_Direct_SetSpeed(axis_num, speed)
        if ret:
            raise RuntimeError(f"axis {axis_index} mission 'Set_Speed' failed, error code{ret}")
        time.sleep(0.1)
        ret, val = self.zaux.ZAux_Direct_GetSpeed(axis_num)
        if ret:
            raise RuntimeError(f"axis {axis_index} mission 'Get_Speed' failed, error code{ret}")
        if speed != int(val.value):
            raise ValueError(f"axis {axis_index} speed is {val.value}, not {speed}")
        self.logger.info(f"axis {axis_index}'s speed change, current speed {speed}")
        return True

    def axis_status(self, axis_index: str):
        """
        detect the specific axis status
        Args:
            axis_index: the axis to execute this function

        Returns: the status code of the axis, 0 for normal

        """
        axis_num = self.axis[axis_index]
        ret, value = self.zaux.ZAux_Direct_GetAxisStatus(axis_num)
        if ret:
            raise RuntimeError(f"axis {axis_index} mission 'Get_Axis_Status' failed, error code{ret}")
        return value.value

    def read_position(self, axis_index: Optional[str] = None):
        """
        get the current position
        Args:
            axis_index: the axis to execute this function, if None, means all axes will execute this function

        Returns: position recorded by the encoder,if axis_index is None -> [x, y, z1, z2]

        """
        if axis_index:
            axis_num = self.axis[axis_index]
            ret, mpos = self.zaux.ZAux_Direct_GetMpos(axis_num)
            if ret:
                raise RuntimeError(f"axis {axis_index} mission 'Get_Mpos' failed, error code{ret}")
            return float('{:.1f}'.format(-mpos.value))
        else:
            position_list = []
            for axis_index, axis_num in self.axis.items():
                ret, mpos = self.zaux.ZAux_Direct_GetMpos(axis_num)
                if ret:
                    raise RuntimeError(f"axis {axis_index} mission 'Get_Mpos' failed, error code{ret}")
                position_list.append(float('{:.1f}'.format(-mpos.value)))
            return position_list

    def _absolute_move(self, axis_index: str, position: float, speed: int = None):
        """
        single-axis absolute move, once failed, flag will plus 1, and whole system will stop until flag returns to 0
        Args:
            axis_index: indicate which axis will move
            position: the absolute position where the specific axis will move to
            speed: moving speed, default value is None, which means the speed is unchanged

        Returns: True, if this function is executed successfully

        """
        if position != self.read_position(axis_index):
            flag_lock.acquire()
            if self.flag == 0:
                flag_lock.release()
                if position > self.max_motion_range[axis_index]:
                    flag_lock.acquire()
                    self.flag += 1
                    flag_lock.release()
                    raise ValueError(f"axis {axis_index} out of motion range: {position}")
                axis_num = self.axis[axis_index]
                if self.axis_status(axis_index) == 0:
                    if speed:
                        self.set_speed(axis_index, speed)
                    ret = self.zaux.ZAux_Direct_Single_MoveAbs(axis_num, position)
                    if ret:
                        flag_lock.acquire()
                        self.flag += 1
                        flag_lock.release()
                        raise RuntimeError(f"axis {axis_index} mission 'Direct_Single_MoveAbs' failed, error code: {ret}")
                    while True:
                        ret, idle = self.zaux.ZAux_Direct_GetIfIdle(axis_num)
                        if ret:
                            flag_lock.acquire()
                            self.flag += 1
                            flag_lock.release()
                            raise RuntimeError(f"axis {axis_index} mission 'Get_If_Idle' failed, error code{ret}")
                        if int(idle.value) == -1:
                            break
                        time.sleep(0.1)
                    if self.read_position(axis_index) != position:
                        flag_lock.acquire()
                        self.flag += 1
                        flag_lock.release()
                        raise RuntimeError(f"axis {axis_index} not move to correct position, current position: {self.read_position(axis_index)}")
                    return True
                else:
                    flag_lock.acquire()
                    self.flag += 1
                    flag_lock.release()
                    raise RuntimeError(f"axis {axis_index}'s status exception: {self.axis_status(axis_index)}")
            else:
                flag_lock.release()
                raise RuntimeError(f"some errors occurred in other axes, current axis: {axis_index}")
    def _relative_move(self, axis_index: str, distance: float, speed: int = None):
        """
        single-axis relative move, based on absolute move
        Args:
            axis_index:
            distance:
            speed:

        Returns:

        """
        target_position = self.read_position(axis_index) + distance
        self._absolute_move(axis_index, target_position, speed)
        self.logger.info(f"axis {axis_index} move to {target_position}")

    def _move_xyz(self, position: list):
        """
        move to a specific coordinate
        Operation_Logic:
            lift axis z1 & z2 to a default safe height, move axis x & y to the specific position, then so do axis z1 & z2
            if axis x & y are already at the specific position, directly move axis z1 & z2
        Args:
            position: [x_coord, y_coord, z1_coord, z2_coord]

        Returns:

        """
        self.logger.info(f'move to x:{position[0]}, y:{position[1]}, z1:{position[2]}, z2:{position[3]}')
        if position[0] == self.read_position('x') and position[1] == self.read_position('y'):
            z1 = threading.Thread(target=self._absolute_move, args=('z1', position[2]))
            z2 = threading.Thread(target=self._absolute_move, args=('z2', position[3]))
            z1.start()
            z2.start()
            z1.join()
            z2.join()
        else:
            z1 = threading.Thread(target=self._absolute_move, args=('z1', self.default_safe_coordinates[2]))
            z2 = threading.Thread(target=self._absolute_move, args=('z2', self.default_safe_coordinates[3]))
            z1.start()
            z2.start()
            z1.join()
            z2.join()
            x = threading.Thread(target=self._absolute_move, args=('x', position[0]))
            y = threading.Thread(target=self._absolute_move, args=('y', position[1]))
            z1 = threading.Thread(target=self._absolute_move, args=('z1', position[2]))
            z2 = threading.Thread(target=self._absolute_move, args=('z2', position[3]))
            x.start()
            y.start()
            x.join()
            y.join()
            z1.start()
            z2.start()
            z1.join()
            z2.join()

    def _reset_flag(self):
        """
        trying to clear the alarm information, if succeeds, flag will reset to 0
        Returns:

        """
        for axis_index, axis_num in self.axis.items():
            if 4194304 <= self.axis_status(axis_index) < 8388608:
                self.output_trigger('clear_alm', onoff=True)
                time.sleep(0.1)
                self.output_trigger('clear_alm', onoff=False)
            if self.axis_status(axis_index) != 0:
                return False
        self.flag = 0
        return True

    def output_trigger(self, op_index: str, onoff: bool):
        """
        change the output signal
        Args:
            op_index: output port number
            onoff: True for on, False for off

        Returns:

        """
        if onoff:
            ret = self.zaux.ZAux_Direct_SetOp(self.op[op_index], 1)
            if ret:
                raise RuntimeError(f"failed to open output: {op_index}")
        else:
            ret = self.zaux.ZAux_Direct_SetOp(self.op[op_index], 0)
            if ret:
                raise RuntimeError(f"failed to close output: {op_index}")

    def ultrasonic(self, runtime=10):
        """

        Args:
            runtime: how long the ultrasonic_relay switch-on

        Returns:

        """
        ret = self.zaux.ZAux_Direct_SetOp(self.op['ultrasonic_relay'], 1)
        if ret:
            raise RuntimeError('failed to initiate the ultrasonic cleaner')
        time.sleep(runtime)
        ret = self.zaux.ZAux_Direct_SetOp(self.op['ultrasonic_relay'], 0)
        if ret:
            raise RuntimeError('failed to stop the ultrasonic cleaner')
        self.logger.info('ultrasonic cleaner action completed')
        return True

    def printer_motor(self, runtime=5):
        """

        Args:
            runtime: how long the printer_motor_relay switch-on

        Returns:

        """
        ret = self.zaux.ZAux_Direct_SetOp(self.op['printer_motor_relay'], 1)
        if ret:
            raise RuntimeError('failed to initiate the printer_motor')
        time.sleep(runtime)
        ret = self.zaux.ZAux_Direct_SetOp(self.op['printer_motor_relay'], 0)
        if ret:
            raise RuntimeError('failed to stop the printer_motor')
        self.logger.info('printer_motor action completed')
