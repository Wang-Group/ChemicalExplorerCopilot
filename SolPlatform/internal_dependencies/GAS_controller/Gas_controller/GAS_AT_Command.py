import serial
import time
import threading

class ATCommand:
    def __init__(self, serial_connection: serial.Serial):
        self.ser = serial_connection
        self.globalLockValue = threading.Lock()

    def send_message(self, AT_command: str, timeout: int = 20):
        """
        Generate the AT_command and send it to the serial port.

        Args:
            AT_command: the AT command of the controller.
            timeout: the timeout limit. Defaults to 20.
        """
        self.ser.read_all()
        self.ser.write(AT_command.encode())
        time_begin = time.time()
        while True:
            receive_message = self.ser.readline()
            if receive_message != b'':
                break
            self.ser.write(bytes(AT_command.encode()))
            time.sleep(0.1)
            if time.time() - time_begin >= timeout:
                raise TimeoutError("Send message time is out!")
        return receive_message

    def GA_Open(self):
        """
        Open the card.
        """
        AT_command = "AT+Open"
        flag = self.send_message(AT_command)
        return flag
    
    def GA_Close(self):
        """
        Close the card.
        """
        AT_command = "AT+Close"
        flag = self.send_message(AT_command)
        return flag

    def GA_Reset(self):
        AT_command = "AT+Reset"
        flag = self.send_message(AT_command)
        return flag

    def GA_AxisOn(self, iAxisNum):
        """
        enable the axis

        Args:
            iAxisNum: axis number
        """
        AT_command = f"AT+AxisOn+{iAxisNum}"
        flag = self.send_message(AT_command)
        return flag
    
    def GA_AxisOff(self, iAxisNum):
        """
        disable the axis

        Args:
            iAxisNum: axis number
        """
        AT_command = f"AT+AxisOff+{iAxisNum}"
        flag = self.send_message(AT_command)
        return flag

    def GA_LmtsOn(self, iAxisNum: int, limitType:int = -1):
        """
        open the limits

        Args:
            iAxisNum: axis number
            limitType: {-1: both positive and negative, 
                         0: only positive,
                         1: only negative}
        """
        AT_command = f"AT+LmtsOn+{iAxisNum}+{limitType}"
        flag = self.send_message(AT_command)
        return flag

    def GA_LmtsOff(self, iAxisNum: int, limitType:int = -1):
        """
        close the limits

        Args:
            iAxisNum: axis number
            limitType: {-1: both positive and negative, 
                         0: only positive,
                         1: only negative}
        """
        AT_command = f"AT+LmtsOff+{iAxisNum}+{limitType}"
        flag = self.send_message(AT_command)
        return flag
    
    def GA_SetHardLimN(self, iAxisNum: int, nIOIndex: int, nCardIndex: int = 0):
        """
        Set the negative hard limits

        Args:
            iAxisNum: axis number
            nIOIndex: the input index
            nCardIndex: the index of control card
        """
        AT_command = f"AT+SetHardLimN+{iAxisNum}+1+{nCardIndex}+{nIOIndex}"
        flag = self.send_message(AT_command)
        return flag
    
    def GA_SetHardLimP(self, iAxisNum: int, nIOIndex: int, nCardIndex: int = 0):
        """
        Set the positive hard limits

        Args:
            iAxisNum: axis number
            nIOIndex: the input index
            nCardIndex: the index of control card
        """
        AT_command = f"AT+SetHardLimP+{iAxisNum}+1+{nCardIndex}+{nIOIndex}"
        flag = self.send_message(AT_command)
        return flag
    
    def GA_SetVel(self, iAxisNum: int, vel: float):
        """
        Set the speed of the axis.

        Args:
            iAxisNum: axis number
            vel: speed in pulse/ms
        """
        AT_command = f"AT+SetVel+{iAxisNum}+{vel}"
        flag = self.send_message(AT_command)
        return flag
    
    def GA_SetPos(self, iAxisNum: int, pos: int):
        """
        Set the target position of the axis.

        Args:
            iAxisNum: axis number
            pos: target position in mm
        """
        AT_command = f"AT+SetPos+{iAxisNum}+{pos}"
        flag = self.send_message(AT_command)
        return flag

    def GA_Update(self, *iAxisNum: int):
        """
        Start the action of axis.
        """
        mask = 0xFF
        if iAxisNum:
            mask = 0
            for axis in iAxisNum:
                mask += 10 ** (axis - 1)
            mask = int('0b' + str(mask).zfill(8), 2)
        AT_command = f"AT+Update+{mask}"
        flag = self.send_message(AT_command)
        return flag

    def GA_Stop(self, *iAxisNum: int, stopType: int = 10):
        """
        Stop the selected axis

        Args:
            iAxisNum: axis number
            stopType: how to stop the axis {10: hard stop, 0: soft stop}
        """
        mask = 0xFF
        if iAxisNum:
            mask = 0
            for axis in iAxisNum:
                mask += 10 ** (axis - 1)
            mask = int('0b' + str(mask).zfill(8), 2)
        AT_command = f"AT+Stop+{mask}+{stopType}"
        flag = self.send_message(AT_command)
        return flag

    def GA_PrfJog(self, iAxisNum):
        """
        Set the axis into Jog(speed) mode.

        Args:
            iAxisNum: axis number
        """
        AT_command = f"AT+PrfJog+{iAxisNum}"
        flag = self.send_message(AT_command)
        return flag
    
    def GA_SetJogPrm(self, iAxisNum: int, dAcc: float, dDec: float, dSmoothTime: int = 0):
        """
        Set the param of jog mode.
        Args:
            iAxisNum: axis number
            dAcc: accelerate of axis
            dDec: decelerate of axis
            dSmoothTime: the smooth time

        Returns:

        """
        AT_command = f"AT+SetJogPrm+{iAxisNum}+{dAcc}+{dDec}+{dSmoothTime}"
        flag = self.send_message(AT_command)
        return flag

    def GA_GetJogPrm(self, iAxisNum):
        """
        Get the jog param of axis
        Args:
            iAxisNum: axis number
        Returns:
            the param of axis number
        """
        AT_command = f"AT+GetJogPrm+{iAxisNum}"
        flag = self.send_message(AT_command)
        return flag
    
    def GA_PrfTrap(self, iAxisNum):
        """
        Prepare for the trap mode.

        Args:
            iAxisNum: axis number
        """
        AT_command = f"AT+PrfTrap+{iAxisNum}"
        flag = self.send_message(AT_command)
        return flag
    
    def GA_SetTrapPrm(self, iAxisNum: int, dAcc: float, dDec: float, dVelStart: float = 0, dSmoothTime: int = 0):
        """
        Set the oaram of trap mode.
        Args:
            iAxisNum: axis number
            dAcc: the accelerate of axis
            dDec: the decelerate of axis
            dVelStart: the start speed
            dSmoothTime: the smooth time

        Returns:

        """
        AT_command = f"AT+SetTrapPrm+{iAxisNum}+{dAcc}+{dDec}+{dVelStart}+{dSmoothTime}"
        flag = self.send_message(AT_command)
        return flag

    def GA_GetTrapPrm(self, iAxisNum: int):
        """

        Args:
            iAxisNum:

        Returns:

        """
        AT_command = f"AT+GetTrapPrm+{iAxisNum}"
        flag = self.send_message(AT_command)
        return flag

    def GA_HomeSns(self, *iAxisNum: int):
        mask = 0
        for axis in iAxisNum:
            mask += 10 ** (axis - 1)
        mask = int('0b' + str(mask).zfill(8), 2)
        AT_command = f"AT+HomeSns+{mask}"
        flag = self.send_message(AT_command)
        return flag

    def GA_HomeSetPrmSingle(self, iAxisNum: int, nHomeMode: int, nHomeDir: int, lOffset: int, 
                            dHomeRapidVel: float, dHomeLocatVel: float, dHomeIndexVel: float, dHomeAcc: float):
        """
        Set the param of datum.

        Args:
            iAxisNum: axis number
            nHomeMode: datum mode. Defaults to 1.
            nHomeDir: datum direction. Defaults to 0.
            lOffset: datum offset. Defaults to 0.
            dHomeRapidVel: the speed of rough datum. Defaults to 10.
            dHomeLocatVel: the speed of accurate datum. Defaults to 3.
            dHomeIndexVel: the speed of find index. Defaults to None.
            dHomeAcc: accelerate of datum. Defaults to 5.
        """
        AT_command = f"AT+HomeSetPrmSingle+{iAxisNum}+{nHomeMode}+{nHomeDir}+{lOffset}+{dHomeRapidVel}+{dHomeLocatVel}+{dHomeIndexVel}+{dHomeAcc}"
        flag = self.send_message(AT_command)
        return flag
    
    def GA_HomeStart(self, iAxisNum: int):
        """
        Start to datum.

        Args:
            iAxisNum: axis number
        """
        self.globalLockValue.acquire()
        AT_command = f"AT+HomeStart+{iAxisNum}"
        flag = self.send_message(AT_command)
        self.globalLockValue.release()
        return flag
    
    def GA_HomeStop(self, iAxisNum: int):
        """
        initiate the axis to return to zero

        Args:
            iAxisNum: axis number
        """
        AT_command = f"AT+HomeStop+{iAxisNum}"
        flag = self.send_message(AT_command)
        return flag

    def GA_HomeGetSts(self, iAxisNum: int):
        """
        stop the axis from returning to zero

        Args:
            iAxisNum: axis number
        """
        AT_command = f"AT+HomeGetSts+{iAxisNum}"
        flag = self.send_message(AT_command)
        return flag

    def GA_GetSts(self, iAxisNum: int):
        """
        get axis status
        Args:
            iAxisNum: axis number
        """
        AT_command = f"AT+GetSts+{iAxisNum}"
        flag = self.send_message(AT_command)
        return flag

    def GA_ClrSts(self, iAxisNum: int):
        """
        clear axis alarm
        Args:
            iAxisNum: axis number
        """
        AT_command = f"AT+ClrSts+{iAxisNum}"
        flag = self.send_message(AT_command)
        return flag
    
    def GA_ZeroPos(self, iAxisNum: int):
        AT_command = f"AT+ZeroPos+{iAxisNum}"
        flag = self.send_message(AT_command)
        return flag

    def GA_SetExtDoValue(self, nValue, nCardIndex=0):
        AT_command = f"AT+SetExtDoValue+{nCardIndex}+{nValue}"
        flag = self.send_message(AT_command)
        return flag

    def GA_SetExtDoBit(self, nBitIndex: int, nValue: int, nCardIndex: int = 0):
        """
        Set the Do (Output) on or off (on: 0 V, off: 24 V)

        Args:
            nBitIndex: the index of Do (output)
            nValue: the switch of Do, e.g. 1 for on, 0 for off
            nCardIndex: the index of control card
        """
        AT_command = f"AT+SetExtDoBit+{nCardIndex}+{nBitIndex}+{nValue}"
        flag = self.send_message(AT_command)
        return flag

    def GA_GetExtDoBit(self, nBitIndex: int, nCardIndex: int = 0):
        """
        Get the status of output.
        Args:
            nCardIndex: the index of control card
            nBitIndex: the index of DO (output)
    
        """
        AT_command = f"AT+GetExtDoBit+{nCardIndex}+{nBitIndex}"
        flag = self.send_message(AT_command)
        return flag
    
    def GA_SetDac(self, nBitIndex: int, voltage: float):
        """
        Set the analog value.

        Args:
            nBitIndex: the index of analog output
            voltage: the analog value of Dac, unit: V
        """
        iValue = round(voltage * 1000)
        AT_command = f"AT+SetDac+{nBitIndex}+{iValue}"
        flag = self.send_message(AT_command)
        return flag
    
    def GA_GetAdc(self, nBitIndex: int):
        """
        Get the analog value.

        Args:
            nBitIndex: the index of analog input
        """
        AT_command = f"AT+GetAdc+{nBitIndex}"
        flag = self.send_message(AT_command)
        return flag