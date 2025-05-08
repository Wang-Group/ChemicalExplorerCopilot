import threading
from .dobot_api import DobotApiDashboard, DobotApi, DobotApiMove, MyType, alarmAlarmJsonFile
from time import sleep
from copy import copy
import numpy as np
import re
import time
import logging



class MG400:
    """
    Control Dobot MG400 robot arm by TCP/IP. Use the commands in ./dobot_api.py.
    Contain the operations of MoveL, MoveJ, SetspeedL, SetspeedJ etc.
    """
    def __init__(self, 
                 ip: str = "192.168.192.6",
                 dashboardPort = 29999,
                 movePort = 30003,
                 feedPort = 30004,
                 logger: logging.Logger = None) -> None:
        """
        :param ip: ip (LAN2)
        :param dashboard: the port of dashboard
        :param moveport: the port of move operation
        :param feed: the port of feed operation
        :param logger: logger
        """
        self.ip = ip
        self.logger = logger
        self.dashboardPort = dashboardPort
        self.movePort = movePort
        self.feedPort = feedPort

        self.current_actual = None
        self.algorithm_queue = None
        self.enableStatus_robot = None
        self.robotErrorState = False
        self.globalLockValue = threading.Lock()


    def initialize_robot(self, 
                         load: float = 0.250, 
                         x_offset: float = 100, 
                         y_offset: float = 0, 
                         z_offset: float = 0):
        """
        Initialize the MG400 Arm. 
        """
        self.ConnectRobot()
        
        print("start enable...")
        self.dashboard.EnableRobot(load, x_offset, y_offset, z_offset)
        print("complete enable:)")
        feed_thread = threading.Thread(target = self.GetFeed )
        feed_thread.setDaemon(True)
        feed_thread.start()

        feed_thread1 = threading.Thread(target = self.ClearRobotError)
        feed_thread1.setDaemon(True)
        feed_thread1.start()
        print("loop...")

    def ConnectRobot(self):
        """
        Connect the arm.
        """
        try:
            print("connecting")
            self.dashboard = DobotApiDashboard(self.ip, self.dashboardPort)
            self.move = DobotApiMove(self.ip, self.movePort)
            self.feed = DobotApi(self.ip, self.feedPort)
            print("connecting to MG400 successful!")
        except Exception as e:
            print("connecting to MG400 failed!")
            raise e
    
    def DisconnectRobot(self):
        """
        Disable and disconnect the arm.
        """
        self.DisableRobot()
        self.dashboard.__del__()

        
    def EnableRobot(self, 
                    load = 0.175, 
                    x = 60, 
                    y = 0, 
                    z = 0):
        """
        Enable the arm.
        :param load: The load of the clamp, kg
        :param x: The x offset, mm
        :param y: The y offset, mm
        :param z: The z offset, mm
        """
        self.load = load
        self.x = x
        self.y = y
        self.z = z
        self.dashboard.EnableRobot(self.load, self.x, self.y, self.z)

    def DisableRobot(self):
        """ 
        Disable the arm.
        """
        self.dashboard.DisableRobot()

    def GetFeed(self):
        '''
        Get feedback of operations.
        '''
        hasRead = 0
        while True:
            data = bytes()
            while hasRead < 1440:
                temp = self.feed.socket_dobot.recv(1440 - hasRead)
                if len(temp) > 0:
                    hasRead += len(temp)
                    data += temp
            hasRead = 0
            feedInfo = np.frombuffer(data, dtype = MyType)
            if hex((feedInfo['test_value'][0])) == '0x123456789abcdef':
                self.globalLockValue.acquire()
                # Refresh Properties
                self.current_actual = feedInfo["tool_vector_actual"][0]
                self.algorithm_queue = feedInfo['isRunQueuedCmd'][0]
                self.enableStatus_robot=feedInfo['EnableStatus'][0]
                self.robotErrorState= feedInfo['ErrorStatus'][0]
                self.globalLockValue.release()
                
            sleep(0.001)

    def WaitArrive(self, point_list: list):
        """
        Wait until the move operation finish.
        """
        while True:
            is_arrive = True
            self.globalLockValue.acquire()
            if self.current_actual is not None:
                for index in range(4):
                    if (abs(self.current_actual[index] - point_list[index]) > 0.5):
                        is_arrive = False
                if is_arrive :
                    self.globalLockValue.release()
                    return
            self.globalLockValue.release()  
            sleep(0.001)

    def ClearRobotError(self):
        """
        Clear the error of the arm when the arm crack.
        """
        dataController,dataServo =alarmAlarmJsonFile()    
        while True:
            self.globalLockValue.acquire()
            if self.robotErrorState:
                        numbers = re.findall(r'-?\d+', self.dashboard.GetErrorID())
                        numbers= [int(num) for num in numbers]
                        if (numbers[0] == 0):
                            if (len(numbers)>1):
                                for i in numbers[1:]:
                                    alarmState=False
                                if i==-2:
                                    self.logger.warning(f"hit the arm! {i}")
                                    alarmState=True
                                if alarmState:
                                    continue                
                                for item in dataController:
                                    if  i==item["id"]:
                                        self.logger.warning(f"controller error id")
                                        alarmState=True
                                        break 
                                if alarmState:
                                    continue
                                for item in dataServo:
                                    if  i==item["id"]:
                                        self.logger.warning("Servo error id")
                                        break 
                                
                                choose = input("enter 1 to remove the errors and continue: ")     
                                if  int(choose) == 1:
                                    self.dashboard.ClearError()
                                    sleep(0.01)
                                    self.dashboard.Continue()

            else:  
                if int(self.enableStatus_robot[0])==1 and int(self.algorithm_queue[0])==0 or self.enableStatus_robot is None:
                    self.dashboard.Continue()
            self.globalLockValue.release()
            sleep(5)
            
    def GetPosition(self):
        """
        Get the position of the arm.
        """
        current_pos = copy(list(self.current_actual)[:4])
        for i in range(len(current_pos)):
            current_pos[i] = round(current_pos[i], 2)
        return current_pos
        
    def SetSpeedJ(self, SpeedJRatio: int):
        """
        Set the speed ratio of operation MoveJ.
        :param SpeedJRatio: the speed ratio of the arm: int, 0-100.
        """
        self.dashboard.SpeedJ(SpeedJRatio)

    def MoveJ(self, point_list: list):
        """
        Run to the position by MoveJ.
        :param point_list: the target coordinate: list
        """
        self.move.MovJ(point_list[0], 
                       point_list[1], 
                       point_list[2], 
                       point_list[3])

        self.WaitArrive(point_list)

    def SetSpeedL(self, SpeedLRatio: int):
        """
        Set the speed ratio of operation MoveL.
        :param SpeedLRatio: the speed ratio of the arm: int, 0-100.
        """
        self.dashboard.SpeedL(SpeedLRatio)

    def MoveL(self, point_list: list):
        """
        Run to the position by MoveL.
        :param point_list: the target coordinate: list
        """
        self.move.MovL(point_list[0], 
                       point_list[1], 
                       point_list[2], 
                       point_list[3])

        self.WaitArrive(point_list)

    def RelMoveL(self, point_list: list, offset_x: float = 0, offset_y: float = 0, offset_z: float = 0, offset_r: float = 0):
        """
        Run to the relative position of target coordinate.
        param point_list: the target coordinate: list
        param offset_x: the x offset of target coordinate: float
        param offset_y: the y offset of target coordinate: float
        param offset_z: the z offset of target coordinate: float
        param offset_r: the r offset of target coordinate: float
        """
        self.move.MovL(point_list[0] + offset_x, 
                       point_list[1] + offset_y, 
                       point_list[2] + offset_z,
                       point_list[3] + offset_r)

    def output_trigger(self, output_index: int, onoff: bool): 
        """
        Open/Close output.

        Args:
            output_index: the index of output
            onoff: the trigger of output
        """
        if onoff: 
            self.dashboard.DO(output_index, 1)
            return True
        else: 
            self.dashboard.DO(output_index, 0)
            return True

    def input_status(self, input_index: int) -> bool: 
        """
        Get the status of input

        Args:
            input_index: the index of input

        Returns:
            True for high signal
            False for low signal
        """
        ip_status = self.dashboard.DI(input_index)[3]

        if ip_status == 0: 
            return False
        elif ip_status == 1:
            return True
        else: 
            raise ValueError(f"unnormal feedback! current value is {ip_status}.")

    def Clamp(self, num : int = 1, status: int = 1):
        """
        Open or close the Clamp.
        param num: the num of robot DO: int
        param status: the status of the clamp: {0: close, 1: open}
        """
        self.dashboard.DO(num, status)

    def initialize_gripper(self, do_num: int = 2):
        self.dashboard.DO(do_num, 1)
        time.sleep(0.1)
        self.dashboard.DO(do_num, 0)
        while True:
            if self.dashboard.DI(1)[3] == "0" and self.dashboard.DI(2)[3] == "1":
                return True
            

    def open_gripper(self, do_num: int = 1):

        self.dashboard.DO(do_num, 0)
        while True:
            if self.dashboard.DI(1)[3] == "0" and self.dashboard.DI(2)[3] == "1":
                return True

    def close_gripper(self, do_num: int = 1):

        self.dashboard.DO(do_num, 1)
        time.sleep(0.5)
        while True:
            if self.dashboard.DI(1)[3] == "1" and self.dashboard.DI(2)[3] == "1":
                self.logger.info("get obj on gripper")
                return True
            elif self.dashboard.DI(1)[3] == "1" and self.dashboard.DI(2)[3] == "0":
                return True
            else:
                self.logger.warning("obj drop from gripper pls check!")
                raise ValueError("obj drop from gripper pls check!")
            