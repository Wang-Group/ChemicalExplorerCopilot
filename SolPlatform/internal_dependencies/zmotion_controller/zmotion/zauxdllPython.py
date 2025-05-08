import ctypes
import platform
import pkg_resources

DLL_PATH = pkg_resources.resource_filename('zmotion', './zauxdll.dll')
# Determine the operating environment
systype = platform.system()
if systype == 'Windows':
    if platform.architecture()[0] == '64bit':
        zauxdll = ctypes.WinDLL(DLL_PATH)
    else:
        zauxdll = ctypes.WinDLL(DLL_PATH)
        print('Windows x86')
elif systype == 'Darwin':
    zmcdll = ctypes.CDLL('./zmotion.dylib')
    print("macOS")
elif systype == 'Linux':
    zmcdll = ctypes.CDLL('./zmotion.so')
    print("Linux")
else:
    print("OS Not Supported!!")


class ZAUXDLL:
    def __init__(self):
        self.handle = ctypes.c_void_p()

    def ZAux_Execute(self, pszCommand):
        '''
        :Description: Encapsulates the Execute function to receive errors.

        :param pszCommand: string command. type: sting

        :param uiResponseLength: Returns the length in characters. type: uint32

        :Return: Error code, returned string. type: int32, sting
        
       '''
        _str = pszCommand.encode('utf-8')
        psResponse = ctypes.c_char_p()
        psResponse.value = b''
        uiResponseLength = 2048
        ret = zauxdll.ZAux_Execute(
            self.handle, _str, psResponse, uiResponseLength)
        rev = psResponse.value.decode('utf-8')
        return ret, rev

    def ZAux_DirectCommand(self, pszCommand):
        '''
        :Description: Encapsulates DirectCommand function to receive errors.

        :param pszCommand: string command. type: sting

        :param uiResponseLength: Returns the length in characters. type: uint32

        :Return: Error code, returned string. type: int32, sting

       '''
        _str = pszCommand.encode('utf-8')
        psResponse = ctypes.c_char_p()
        psResponse.value = b''
        uiResponseLength = 2048
        ret = zauxdll.ZAux_DirectCommand(
            self.handle, _str, psResponse, uiResponseLength)
        rev = psResponse.value.decode('utf-8')
        return ret, rev

    def ZAux_OpenEth(self, ipaddr):
        '''
        :Description: Establish a link with the controller.

        :param ipaddress: IP address, input as a string. type: sting

        :Return: Error code. type: int32

        '''
        ip_bytes = ipaddr.encode('utf-8')
        p_ip = ctypes.c_char_p(ip_bytes)
        ret = zauxdll.ZAux_OpenEth(p_ip, ctypes.pointer(self.handle))
        return ret

    def ZAux_SearchEthlist(self, address_buff_length, ms):
        #  '''
        # :Description: Search for IP addresses in the current network segment. .
        #
        # :param addrbufflength: Total length of IP addresses returned by the search type: uint32
        #
        # :param ms: Search timeout. type: uint32
        #
        # :Return,Ipaddrlist: Error code, All IP addresses searched type: sting
        #
        # '''

        # ip_address_list = ctypes.c_char_p(ip_address_list.encode('utf-8'))
        address_buff_length = ctypes.c_uint32(address_buff_length)
        ms = ctypes.c_uint32(ms)
        ip = ctypes.c_char_p("".encode('utf-8'))
        ret = zauxdll.ZAux_SearchEthlist(ip, address_buff_length, ms)
        return ret, ip

    def ZAux_SearchEth(self, ipaddress, uims):
        #  '''
        # :Description: Quickly search for controllers.
        #
        # :param ipaddress: Controller IP address. type: sting
        #
        # :param uims: Response time. type: uint32
        #
        # :Return: Error code, ERR_OK means it was found. type: int32
        #
        # '''
        ip_bytes = ipaddress.encode('utf-8')
        p_ip = ctypes.c_char_p(ip_bytes)
        ret = zauxdll.ZAux_SearchEth(
            p_ip, ctypes.c_int(uims), ctypes.pointer(self.handle))
        return ret

    def ZAux_OpenCom(self, comid):
        '''
        :Description: Establish a link with the controller, serial port mode.

        :param comid: serial port number type: uint32

        :Return: error code. type: int32

        '''
        ret = zauxdll.ZAux_OpenCom(ctypes.c_uint32(
            comid), ctypes.pointer(self.handle))
        return ret

    def ZAux_Close(self):
        '''
        :Description: Close the controller link.

        :Return: Error code. type: int32

        '''
        ret = zauxdll.ZAux_Close(self.handle)
        return ret

    def ZAux_Direct_GetAD(self, ionum):
        '''
        :Description: Read analog input signal.

        :param ionum: AIN port number. type: int

        :Return: Error code, returned analog value 0-4095 for 4 series or below. type: int32, folat

       '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetAD(
            self.handle, ctypes.c_int(ionum), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetDA(self, ionum, fValue):
        '''
        :Description: Open analog output signal.

        :param ionum: DA output port number. type: int

        :param fValue: Set analog value 0-4095 below 4 series. type: float

        :Return: Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_SetDA(
            self.handle, ctypes.c_int(ionum), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetDA(self, ionum):
        '''
        :Description: Read the status of the analog output port.

        :param ionum: analog output port number. type: int

        :Return: error code, returned analog value 0-4095 for 4 series or below. type: int32, float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetDA(
            self.handle, ctypes.c_int(ionum), ctypes.byref(value))
        return ret, value

    def ZAux_SearchAndOpenCom(self, uimincomidfind, uimaxcomidfind, uims):
        '''
        :Description: Quick controller to establish a link.

        :param uimincomidfind: Minimum serial port number. type: uint32

        :param uimincomidfind: Maximum serial port number. type: uint32

        :param uims: Link time. type: uint32

        :Return: Error code, valid COM, card link handle. type: int32,uint

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_SearchAndOpenCom(ctypes.c_uint32(uimincomidfind), ctypes.c_uint32(uimaxcomidfind),
                                            ctypes.byref(value), uims, ctypes.pointer(self.handle))
        return ret, value

    def ZAux_OpenEth(self, ipaddr):
        '''
        :Description: Establish a link with the controller.

        :param ipaddr: IP address, input as a string. type: sting

        :Return: Error code. type: int32

        '''
        ip_bytes = ipaddr.encode('utf-8')
        p_ip = ctypes.c_char_p(ip_bytes)
        ret = zauxdll.ZAux_OpenEth(p_ip, ctypes.pointer(self.handle))
        return ret

    def ZAux_SetComDefaultBaud(self, dwBaudRate, dwByteSize, dwParity, dwStopBits):
        '''
        :Description: You can modify the default baud rate and other settings.

        :param dwBaudRate: Baud rate. type: uint32

        :param dwParity: NOPARITY, parity bit. type: uint32

        :param dwStopBits: ONESTOPBIT stop bit. type: uint32

        :Return: Error code. type: int32

       '''
        ret = zauxdll.ZAux_SetComDefaultBaud(ctypes.c_uint32(dwBaudRate), ctypes.c_uint32(dwByteSize),
                                             ctypes.c_uint32(dwParity), ctypes.c_uint32(dwStopBits))
        return ret

    def ZAux_SetIp(self, ipaddress):
        '''
        :Description: Modify the controller IP address.

        :param ipaddress: IP address. type: sting

        :Return: Error code. type: int32

        '''
        ip_bytes = ipaddress.encode('utf-8')
        p_ip = ctypes.c_char_p(ip_bytes)
        ret = zauxdll.ZAux_SetIp(self.handle, p_ip)
        return ret

    def ZAux_Resume(self):
        '''
        :Description: Pause the BAS project.

        :Return: Error code. type: int32

        '''
        ret = zauxdll.ZAux_Resume(self.handle)
        return ret

    def ZAux_Pause(self):
        '''
        :Description: Pause the BAS program in the controller

        :Return: Error code. type: int32

        '''
        ret = zauxdll.ZAux_Pause(self.handle)
        return ret

    def ZAux_BasDown(self, Filename, run_mode):
        '''
        :Description: Single BAS file generates ZAR and downloads it to the controller for running.

        :param Filename: BAS file path. type: sting

        :param run_mode: 0-RAM 1-ROM. type: uint32

        :Return: Error code. type: int32
        '''
        _str = Filename.encode('utf-8')
        ret = zauxdll.ZAux_BasDown(
            self.handle, _str, run_mode, ctypes.pointer(self.handle))
        return ret

    def ZAux_Direct_GetIn(self, ionum):
        '''
        :Description: Read input signal.

        :param ionum: IN number. type: int

        :Return: Error code, input port status. type: int32, uint32

        '''
        value = ctypes.c_int32()
        ret = zauxdll.ZAux_Direct_GetIn(
            self.handle, ctypes.c_int(ionum), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetOp(self, ionum, iValue):
        '''
        :Description: Turn on the output signal.

        :param ionum: Output port number. type: int

        :param iValue: Output port status. type: uint32

        :Return: Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetOp(self.handle, ionum, iValue)
        return ret

    def ZAux_Direct_GetOp(self, ionum):
        '''
        :Description: Read the output port status.

        :param ionum: output port number. type: int

        :Return: error code, output port status. type: int32,uint32

        '''
        value = ctypes.c_int32()
        ret = zauxdll.ZAux_Direct_GetOp(
            self.handle, ctypes.c_int(ionum), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetInvertIn(self, ionum, bifInvert):
        '''
        :Description: Set the input port inversion.

        :param ionum: Output port number. type: int

        :param bifInvert: Inversion status 0/1. type: int

        :Return: Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_SetInvertIn(self.handle, ionum, bifInvert)
        return ret

    def ZAux_Direct_GetInvertIn(self, ionum):
        '''
        :Description: Read the input port reversal status.

        :param ionum: output port number. type: int

        :Return: error code, reversal status. type: int32 ,int

        '''
        value = ctypes.c_int32()
        ret = zauxdll.ZAux_Direct_GetInvertIn(
            self.handle, ctypes.c_int(ionum), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetPwmFreq(self, ionum, fValue):
        '''
        :Description: Set the pwm frequency.

        :param ionum:PWM number port. type: int

        :param fValue: Frequency Hardware PWM1M Soft PWM 2K. type: float

        :Return:Error code. type: int32

       '''
        ret = zauxdll.ZAux_Direct_SetPwmFreq(
            self.handle, ctypes.c_int(ionum), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_SetPwmDuty(self, ionum, fValue):
        '''
        :Description: Set the pwm duty cycle.

        :param ionum:PWM number port. type: int

        :param fValue: Duty change 0-1 0 means closing the PWM port. type: float

        :Return:Error code. type: int32: int32

        '''

        ret = zauxdll.ZAux_Direct_SetPwmDuty(
            self.handle, ctypes.c_int(ionum), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetPwmDuty(self, ionum):
        '''
        :Description: Set the pwm duty cycle.

        :param ionum:PWM number port. type: int

        :Return:Error code, return empty ratio. type: int32,float

        '''

        ret = zauxdll.ZAux_Direct_SetPwmDuty(self.handle, ctypes.c_int(ionum))
        return ret

    def ZAux_Direct_GetPwmFreq(self, ionum):
        '''
        :Description: Read the pwm frequency.

        :param ionum:PWM number port. type: int

        :Return: Error code, return frequency. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetPwmFreq(
            self.handle, ctypes.c_int(ionum), ctypes.byref(value))
        return ret, value

    def ZAux_GetModbusIn(self, ionumfirst, ionumend):
        '''
        :Description: Parameters Quickly read multiple inputs.

        :param ionumfirst:IN start number. type: int

        :param ionumend:IN end number. type: int

        :Return: Error code, bit status is stored bitwise. type: int32,uint8

        '''
        value = ctypes.c_int8()
        ret = zauxdll.ZAux_GetModbusIn(self.handle, ctypes.c_int(ionumfirst), ctypes.c_int(ionumend),
                                       ctypes.byref(value))
        return ret, value

    def ZAux_GetModbusOut(self, ionumfirst, ionumend):
        '''
        :Description: Parameters Quickly read multiple current output statuses.

        :param ionumfirst:IN start number. type: int

        :param ionumend:IN end number. type: int

        :Return: Error code, bit status is stored bitwise. type: int32,uint8red bitwise. type: int32,uint8

        '''
        value = ctypes.c_int8()
        ret = zauxdll.ZAux_GetModbusOut(self.handle, ctypes.c_int(ionumfirst), ctypes.c_int(ionumend),
                                        ctypes.byref(value))
        return ret, value

    def ZAux_GetModbusDpos(self, imaxaxises):
        '''
        :Description: Parameters Quickly read multiple current DPOSs.

        :param imaxaxises:Axis number type: int

        :Return:Error code, the coordinate value read starts from axis 0. type: int32,float

        '''
        value = (ctypes.c_float * imaxaxises)()
        ret = zauxdll.ZAux_GetModbusDpos(self.handle, imaxaxises, value)
        return ret, value

    def ZAux_GetModbusMpos(self, imaxaxises):
        '''
        :Description: Parameters Quickly read multiple current MPOS.

        :param imaxaxises:Axis number type: int

        :Return:Error code, the feedback coordinate value read starts from axis 0. type: int32,float

        '''
        value = (ctypes.c_float * imaxaxises)()
        ret = zauxdll.ZAux_GetModbusMpos(self.handle, imaxaxises, value)
        return ret, value

    def ZAux_GetModbusCurSpeed(self, imaxaxises):
        '''
        :Description: Parameters Quickly read multiple current speeds.

        :param imaxaxises:Axis number type: int

        :Return: Error code, the current speed of reading starts from axis 0. type: int32,float

        '''
        value = (ctypes.c_float * imaxaxises)()
        ret = zauxdll.ZAux_GetModbusCurSpeed(self.handle, imaxaxises, value)
        return ret, value

    def ZAux_Direct_SetAccel(self, iaxis, fValue):
        '''
        :Description: Set acceleration.

        :param iaxis:Axle number   type: int

        :param fValue:Set value type: float

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_SetAccel(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_SetParam(self, sParam, iaxis, fset):
        '''
        :Description: General parameter modification function sParam: Fill in the parameter name.

        :param sParam:axis parameter name "DPOS" ... type: sting

        :param iaxis:Axle number   type: int

        :param fset:set value type: float

        :Return:Error code. type: int32

        '''
        _str = sParam.encode('utf-8')
        ret = zauxdll.ZAux_Direct_SetParam(
            self.handle, _str, ctypes.c_int(iaxis), ctypes.c_float(fset))
        return ret

    def ZAux_Direct_GetParam(self, sParam, iaxis):
        '''
        :Description:Use parameter Common parameter reading function, sParam:Fill in the parameter name.

        :param sParam:axis parameter name "DPOS" ... type: sting

        :param iaxis:Axle number   type: int

        :Return:Error code, read return value. type: int32,float

        '''
        value = ctypes.c_float()
        _str = sParam.encode('utf-8')
        ret = zauxdll.ZAux_Direct_GetParam(
            self.handle, _str, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetAccel(self, iaxis):
        '''
        :Description: Read acceleration.

        :param sParam:Axle number. type: int

        :Return: Error code, acceleration return value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetAccel(
            self.handle, iaxis, ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetAddax(self, iaxis):
        '''
        :Description: Read the overlay axis.

        :param iaxis:Axle number.         type:int

        :Return:Error code, read axis superimposed axis number. type: int32,float

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetAddax(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetAlmIn(self, iaxis, iValue):
        '''
        :Description: Set the axis alarm signal.

        :param iaxis:Axle number. type: int

        :param iValue: alarm signal input port number, set -1 type: int

        :Return:Error code. type: int32
        '''

        ret = zauxdll.ZAux_Direct_SetAlmIn(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetAlmIn(self, iaxis):
        '''
        :Description: Read the alarm signal.

        :param iaxis:Axle number.   type:int

        :Return: Error code, return value of the alarm signal input port. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetAlmIn(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetAtype(self, iaxis, iValue):
        '''
        :Description: Set the axis type.

        :param iaxis:Axle number. type: int

        :param iValue:axis type. type: int

        :Return:Error code. type: int32
        '''

        ret = zauxdll.ZAux_Direct_SetAtype(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetAtype(self, iaxis):
        '''
        :Description: Read the axis type.

        :param iaxis:Axle number.     type:int

        :Return:Error code, axis type return value. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetAtype(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetAxisStatus(self, iaxis):
        '''
        :Description: Read the axis state.

        :param iaxis:Axle number.         type:int

        :Return: Error code, axis status return value. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetAxisStatus(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetAxisAddress(self, iaxis, piValue):
        '''
        :Description: Set the axis address.

        :param iaxis:Axle number. type: int

        :param piValue: axis address setting value. type: int

        :Return:Error code. type: int32
        '''

        ret = zauxdll.ZAux_Direct_SetAxisAddress(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(piValue))
        return ret

    def ZAux_Direct_GetAxisAddress(self, iaxis):
        '''
        :Description: Read the axis address.

        :param iaxis:Axis number.         type:int

        :Return:Error code, axis address return value. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetAxisAddress(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetAxisEnable(self, iaxis, iValue):
        '''
        :Description: Set axis enable (only valid for bus controller axes).

        :param iaxis:Axle number. type: int

        :param iValue: Status 0-Close 1-Open. type: int

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_SetAxisEnable(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetAxisEnable(self, iaxis):
        '''
        :Description: Read the axis enable state.

        :param iaxis:Axle number.         type:int

        :Return: Error code, return enabled status. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetAxisEnable(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetClutchRate(self, iaxis, fValue):
        '''
        :Description: Set the link rate.

        :param iaxis:Axle number. type: int

        :param fValue: Synchronous connection rate. type: float

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_SetClutchRate(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetClutchRate(self, iaxis):
        '''
        :Description: Read link rate.

        :param iaxis:Axis number.         type:int

        :Return:Error code, connection rate return value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetClutchRate(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetCloseWin(self, iaxis, fValue):
        '''
        :Description: Sets the end coordinate range point of the latch trigger.

        :param iaxis:Axis number. type: int

        :param fValue: Set range value. type: float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetCloseWin(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetCloseWin(self, iaxis):
        '''
        :Description: Read the end coordinate range point of the latch trigger.

        :param iaxis:Axis number.         type:int

        :Return:Error code, return range value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetCloseWin(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetCornerMode(self, iaxis, iValue):
        '''
        :Description: Set corner deceleration.

        :param iaxis:Axis number.         type:int

        :param iValue: Corner deceleration mode. type:int

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_SetCornerMode(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetCornerMode(self, iaxis):
        '''
        :Description: Read corner deceleration.

        :param iaxis:Axis number.         type:int

        :Return: Error code, return corner mode. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetCornerMode(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetCreep(self, iaxis, fValue):
        '''
        :Description: Set the crawling speed back to zero.

        :param iaxis:Axis number.         type:int

        :param fValue: Set speed value. type:float

        :Return:Error code. type: int32

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_SetCreep(self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue),
                                           ctypes.byref(value))
        return ret

    def ZAux_Direct_GetCreep(self, iaxis):
        '''
        :Description: Read back to zero crawling speed.

        :param iaxis:Axis number.         type:int

        :Return:Error code, return crawling speed value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetCreep(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetDatumIn(self, iaxis, iValue):
        '''
        :Description: Set the origin signal Set-1 to cancel the origin setting.

        :param axis: axis number. typee:int

        :param iValue: The set origin signal input Entrance number。  type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetDatumIn(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetDatumIn(self, iaxis):
        '''
        :Description: Read the origin signal.

        :param iaxis:Axis number.         type:int

        :Return:Error code, return to the origin input number. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetDatumIn(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetDecel(self, iaxis, fValue):
        '''
        :Description: Set the deceleration.

        :param iaxis:Axis number.         type:int

        :param fValue: The deceleration value set. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetDecel(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetDecel(self, iaxis):
        '''
        :Description:Read deceleration

        :param iaxis:Axis number.         type:int

        :Return: Error code, set deceleration return value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetDecel(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetDecelAngle(self, iaxis, fValue):
        '''
        :Description: Set the corner deceleration angle, start deceleration angle, unit in radians.

        :param iaxis:Axis number.         type:int

        :param fValue: Set corner deceleration angle. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetDecelAngle(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetDecelAngle(self, iaxis):
        '''
        :Description: Read the angle of the corner to start deceleration, in radians.

        :param iaxis:Axis number.         type:int

        :Return: Error code, return corner deceleration angle. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetDecelAngle(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetDpos(self, iaxis, fValue):
        '''
        :Description: Set the axis position.

        :param iaxis:Axis number.         type:int

        :param fValue: The coordinate value set. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetDpos(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetDpos(self, iaxis):
        '''
        :Description: Read the axis position.

        :param iaxis:Axis number.         type:int

        :Return:Error code, return command position coordinate. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetDpos(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetEncoder(self, iaxis):
        '''
        :Description: Read the internal encoder value (the absolute value position when the bus absolute value is servo).

        :param iaxis:Axis number.         type:int

        :Return:Error code, the returned internal encoder value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetEncoder(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetEndMove(self, iaxis):
        '''
        :Description: Read the final position of the current motion.

        :param iaxis:Axis number.         type:int

        :Return:Error code, the final position returned. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetEndMove(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetEndMoveBuffer(self, iaxis):
        '''
        :Description: Reads the final position of the current and buffered motion, which can be used for relatively absolute conversion.

        :param iaxis:Axis number.         type:int

        :Return:Error code, the final position returned. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetEndMoveBuffer(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetEndMoveSpeed(self, iaxis, fValue):
        '''
        :Description: Sets the end speed of SP motion.

        :param iaxis:Axis number.         type:int

        :param fValue: Set speed value. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetEndMoveSpeed(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetEndMoveSpeed(self, iaxis):
        '''
        :Description: Read the end speed of SP motion.

        :param iaxis:Axis number.         type:int

        :Return: Error code, return speed value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetEndMoveSpeed(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetErrormask(self, iaxis, iValue):
        '''
        :Description: Set the error flag, and AXISSTATUS do operations with operations to determine which errors need to be turned off WDOG.

        :param iaxis:Axis number.         type:int

        :param iValue: Set the value. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetErrormask(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetErrormask(self, iaxis):
        '''
        :Description: Read the error mark, and AXISSTATUS do operations with operations to determine which errors need to be turned off WDOG.

        :param iaxis:Axis number.         type:int

        :Return:Error code, returned mark value. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetErrormask(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetFastJog(self, iaxis, iValue):
        '''
        :Description: Sets the fast JOG input.

        :param iaxis:Axis number.         type:int

        :param iValue: Fast JOG input port number. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetFastJog(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetFastJog(self, iaxis):
        '''
        :Description: Read fast JOG input.

        :param iaxis:Axis number.         type:int

        :Return: Error code, return JOG input port number. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetFastJog(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetFastDec(self, iaxis, fValue):
        '''
        :Description: Sets the fast deceleration.

        :param iaxis:Axis number.         type:int

        :param fValue: Set fast deceleration. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetFastDec(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetFastDec(self, iaxis):
        '''
        :Description: Read fast deceleration.

        :param iaxis:Axis number.         type:int

        :Return: Error code, return fast deceleration. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetFastDec(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetFe(self, iaxis):
        '''
        :Description: Read the follow-up error.

        :param iaxis:Axis number.         type:int

        :Return: Error code, return follow-up error. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetFe(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetFeLimit(self, iaxis, fValue):
        '''
        :Description: Set the maximum allowed follow-up error value.

        :param iaxis:Axis number.         type:int

        :param fValue: The maximum error value set. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetFeLimit(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetFeLimit(self, iaxis):
        '''
        :Description: Read the maximum allowed follow-up error value.

        :param iaxis:Axis number.         type:int

        :Return: Error code, the maximum error value returned. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetFeLimit(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetFRange(self, iaxis, fValue):
        '''
        :Description: Set the follow-up error value during alarm.

        :param iaxis:Axis number.         type:int

        :param fValue: The error value set. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetFRange(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetFeRange(self, iaxis):
        '''
        :Description: Following error value when reading the alarm.

        :param iaxis:Axis number.         type:int

        :Return: Error code, the returned alarm error value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetFeRange(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetFholdIn(self, iaxis, iValue):
        '''
        :Description: Set to keep input.

        :param iaxis:Axis number.         type:int

        :param fValue: The input port number set. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetFholdIn(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetFholdIn(self, iaxis):
        '''
        :Description: Read and hold input.

        :param iaxis:Axis number.         type:int

        :Return: Error code, return to input HOLDIN input port number. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetFholdIn(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetFhspeed(self, iaxis, pfValue):
        '''
        :Description: Set the axis holding speed.

        :param iaxis:Axis number.         type:int

        :param fValue: The speed value set. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetFhspeed(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(pfValue))
        return ret

    def ZAux_Direct_GetFhspeed(self, iaxis):
        '''
        :Description: Read the axis to maintain speed.

        :param iaxis:Axis number.         type:int

        :Return: Error code, return hold speed. type: int32,int

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetFhspeed(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetForceSpeed(self, iaxis, fValue):
        '''
        :Description: Sets the running speed of SP motion.

        :param iaxis:Axis number.         type:int

        :param fValue: The speed value set. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetForceSpeed(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetForceSpeed(self, iaxis):
        '''
        :Description: Read the running speed of SP motion.

        :param iaxis:Axis number.         type:int

        :Return:Error code, returns the SP motion speed value. type: int32,int

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetForceSpeed(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetFsLimit(self, iaxis, fValue):
        '''
        :Description: Set the forward soft limit, and set a larger value when cancelled.

        :param iaxis:Axis number.         type:int

        :param fValue: The limit value set. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetFsLimit(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetFsLimit(self, iaxis):
        '''
        :Description: Read the forward soft limit.

        :param iaxis:Axis number.         type:int

        :Return:Error code, return forward limit coordinate. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetFsLimit(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetFullSpRadius(self, iaxis, fValue):
        '''
        :Description: Set the minimum radius of the small circle speed limit.

        :param iaxis:Axis number.         type:int

        :param fValue: The minimum radius set. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetFullSpRadius(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetFullSpRadius(self, iaxis):
        '''
        :Description: Read the minimum radius of the speed limit of small circles.

        :param iaxis:Axis number.         type:int

        :Return: Error code, return speed limit radius. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetFullSpRadius(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetFwdIn(self, iaxis, iValue):
        '''
        :Description: Set forward hard limit input When set to -1, it means that no limit is set.

        :param iaxis:Axis number.         type:int

        :param iValue: Set limit input port number. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetFwdIn(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetFwdIn(self, iaxis):
        '''
        :Description: Read forward hard limit input.

        :param iaxis:Axis number.         type:int

        :Return:Error code, return the forward limit input port number. type: int32,float

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetFwdIn(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetFwdJog(self, iaxis, iValue):
        '''
        :Description: Set forward JOG input.

        :param iaxis:Axis number.         type:int

        :param iValue: Set JOG input port number. type:int

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_SetFwdJog(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetFwdJog(self, iaxis):
        '''
        :Description: Read forward JOG input.

        :param iaxis:Axis number.         type:int

        :Return: Error code, return JOG input port number. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetFwdJog(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetIfIdle(self, iaxis):
        '''
        :Description: Read whether the axis has ended motion.

        :param iaxis:Axis number.         type:int

        :Return: Error code, return to running state 0-Movement -1 Stop. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetIfIdle(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetInvertStep(self, iaxis, iValue):
        '''
        :Description: Set pulse output mode.

        :param iaxis:Axis number.         type:int

        :param iValue: Set pulse output mode Pulse + direction/double pulse. type:int

        :Return:Error code. type: int32
        '''

        ret = zauxdll.ZAux_Direct_SetInvertStep(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetInvertStep(self, iaxis):
        '''
        :Description: Read pulse output mode.

        :param iaxis:Axis number.         type:int

        :Return: Error code, return pulse mode. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetInvertStep(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetInterpFactor(self, iaxis, iValue):
        '''
        :Description: Set whether the interpolation axis participates in speed calculation, default participation (1). This parameter only works on the third axis of the straight line and the spiral.

        :param iaxis:Axis number.         type:int

        :param iValue: Mode 0-No parameter 1- Participate. type:int

        :Return:Error code. type: int32
        '''

        ret = zauxdll.ZAux_Direct_SetInterpFactor(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetInterpFactor(self, iaxis):
        '''
        :Description: Whether the axis participates in the speed calculation when reading interpolation, the default participation is (1). This parameter only works on the third axis of the straight line and the helix.

        :param iaxis:Axis number.         type:int

        :Return: Error code, return speed calculation mode. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetInterpFactor(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetJogSpeed(self, iaxis, fValue):
        '''
        :Description: Set the speed when JOG.

        :param iaxis:Axis number.         type:int

        :param fValue: Set speed value. type:float

        :Return:Error code. type: int32
        '''

        ret = zauxdll.ZAux_Direct_SetJogSpeed(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetJogSpeed(self, iaxis):
        '''
        :Description: Whether the axis participates in the speed calculation when reading interpolation, the default participation is (1). This parameter only works on the third axis of the straight line and the helix.

        :param iaxis:Axis number.         type:int

        :Return: Error code, return speed calculation mode. type: int32,int

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetJogSpeed(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetLoaded(self, iaxis):
        '''
        :Description: Read whether there is buffering in addition to the current motion.

        :param iaxis:Axis number.         type:int

        :Return:Error code, return status value -1 No remaining function 0-There is still remaining motion. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetLoaded(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetLinkax(self, iaxis):
        '''
        :Description: Read the reference axis number of the current link motion.

        :param iaxis:Axis number.         type:int

        :Return:Error code, return the reference axis number of the link. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetLinkax(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetLspeed(self, iaxis, fValue):
        '''
        :Description: Set the axis starting speed.

        :param iaxis:Axis number.         type:int

        :param fValue: Set speed value. type:float

        :Return:Error code. type: int32
        '''

        ret = zauxdll.ZAux_Direct_SetLspeed(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetLspeed(self, iaxis):
        '''
        :Description: Read the axis starting speed.

        :param iaxis:Axis number.         type:int

        :Return:Error code, the returned starting speed value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetLspeed(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetHomeWait(self, iaxis, fValue):
        '''
        :Description: Set the reset to zero and find the waiting time.

        :param axis: axis number. type:int

        :param fValue: Return to zero and find the waiting time MS. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetHomeWait(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(fValue))
        return ret

    def ZAux_Direct_GetHomeWait(self, iaxis):
        '''
        :Description: Read back to zero and find the waiting time.

        :param iaxis:Axis number.         type:int

        :Return: Error code, the returned anti-finding waiting time. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetHomeWait(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetMark(self, iaxis):
        '''
        :Description: Read the encoder latch teaching return status.

        :param axis: axis number. type:int

        :Return: Error code, returned latch trigger status -1-latch trigger 0-not triggered. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetMark(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetMarkB(self, iaxis):
        '''
        :Description: Read the encoder latch b returns the status.

        :param axis: axis number. type:int

        :Return: Error code, returned latch trigger status -1-latch trigger 0-not triggered. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetMarkB(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetMaxSpeed(self, iaxis, iValue):
        '''
        :Description: Set the maximum frequency of pulse output.

        :param axis: axis number. type:int

        :param iValue: The maximum pulse frequency set type:int

        :Return:Error code. type: int32,int32,int

        '''

        ret = zauxdll.ZAux_Direct_SetMaxSpeed(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetMaxSpeed(self, iaxis):
        '''
        :Description: The maximum frequency of the pulse output is read.

        :param axis: axis number. type:int

        :Return: Error code, the returned pulse frequency. type:int32,int
        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetMaxSpeed(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetMerge(self, iaxis, iValue):
        '''
        :Description: Set continuous interpolation.

        :param axis: axis number. type:int

        :param iValue: Continuous interpolation switch 0-Off Continuous interpolation 1-Off Continuous interpolation. type:int

        :Return: Error code, the returned anti-finding waiting time. type: int32,int

        '''
        ret = zauxdll.ZAux_Direct_SetMerge(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetMerge(self, iaxis):
        '''
        :Description: Read the continuous interpolation state.

        :param axis: axis number. type:int

        :Return: Error code, the returned continuous interpolation switch status. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetMerge(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetMovesBuffered(self, iaxis):
        '''
        :Description: Read the number of motion currently buffered.

        :param axis: axis number. type:int

        :Return: Error code, buffer motion number. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetMovesBuffered(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetMoveCurmark(self, iaxis):
        '''
        :Description: Read the MOVE_MARK label of the currently moving command.

        :param axis: axis number. type:int

        :Return: Error code, current MARK label. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetMoveCurmark(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetMovemark(self, iaxis, iValue):
        '''
        :Description: Set the MOVE_MARK label of the motion command. Whenever a motion enters the axis motion buffer, MARK automatically +1.

        :param axis: axis number. type:int

        :param iValue: Set MARK value. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetMovemark(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_SetMpos(self, iaxis, fValue):
        '''
        :Description: Set the feedback position.

        :param axis: axis number. type:int

        :param fValue: Set feedback position. type:float

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_SetMpos(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetMpos(self, iaxis):
        '''
        :Description: Read feedback position.

        :param axis: axis number. type:int

        :Return:Error code, return axis feedback position coordinate. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetMpos(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetMspeed(self, iaxis):
        '''
        :Description:Read feedback speed.

        :param axis: axis number. type:int

        :Return: Error code, return encoder feedback speed. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetMspeed(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetMtype(self, iaxis):
        '''
        :Description: Read the currently moving instruction type.

        :param axis: axis number. type:int

        :Return:Error code, returns the current motion type. type: int32,int
        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetMtype(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetOffpos(self, iaxis, fValue):
        '''
        :Description: Set the offset position to modify.

        :param axis: axis number. type:int

        :param fValue: Set feedback position. type:float

        :Return:Error code. type: int32
        '''

        ret = zauxdll.ZAux_Direct_SetOffpos(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetOffpos(self, iaxis):
        '''
        :Description: Read the modified offset position.
        :param axis: axis number. type:int

        :Return:Error code, return offset coordinate value type: int32, float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetOffpos(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetOpenWin(self, iaxis, fValue):
        '''
        :Description: Sets the end coordinate range point of the latch trigger.

        :param axis: axis number. type:int

        :param fValue: The coordinate value set. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetOpenWin(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetOpenWin(self, iaxis):
        '''
        :Description: Read the end coordinate range point of the latch trigger.

        :param axis: axis number. type:int

        :Return:Error code, return end coordinate value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetOpenWin(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetRegPos(self, iaxis):
        '''
        :Description:Read the measurement feedback position (MPOS) returned to the latch.

        :param axis: axis number. type:int

        :Return:Error code, latched coordinate position. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetRegPos(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetRegPosB(self, iaxis):
        '''
        :Description:Read the measurement feedback position (MPOS) returned to the latch.

        :param axis: axis number. type:int

        :Return:Error code, latched coordinate position. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetRegPosB(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetRemain(self, iaxis):
        '''
        :Description: Read the distance that the return axis has not completed.

        :param axis: axis number. type:int

        :Return:Error code, the remaining distance returned. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetRemain(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetRemain_LineBuffer(self, iaxis):
        '''
        :Description: Parameters The remaining buffer of the axis is calculated as a straight line segment.

        :param axis: axis number. type:int

        :Return: Error code, remaining linear buffer number. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetRemain_LineBuffer(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetRemain_Buffer(self, iaxis):
        '''
        :Description: Parameters The buffer remaining on the axis is calculated as the most complex spatial arc.

        :param axis: axis number. type:int

        :Return: Error code, remaining buffer number. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetRemain_Buffer(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetRepDist(self, iaxis, fValue):
        '''
        :Description: Sets the end coordinate range point of the latch trigger.

        :param axis: axis number. type:int

        :param fValue: The coordinate value set. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetRepDist(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetRepDist(self, iaxis):
        '''
        :Description: Read the coordinates of the DPOS and MPOS automatically cycle the axis according to the REP_OPTION setting.

        :param axis: axis number. type:int

        :Return:Error code, return loop coordinate value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetRepDist(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetRepOption(self, iaxis, iValue):
        '''
        :Description: Set the coordinates and repeat settings.

        :param axis: axis number. type:int

        :param iValue: Mode. type:int

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_SetRepOption(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetRepOption(self, iaxis):
        '''
        :Description: Read coordinates and repeat settings.

        :param axis: axis number. type:int

        :Return:Error code, return mode. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetRepOption(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetRevIn(self, iaxis, iValue):
        '''
        :Description: Set the input point number corresponding to the negative hardware limit switch, -1 is invalid.

        :param axis: axis number. type:int

        :param iValue: The input port number set. type:int

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_SetRevIn(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetRevIn(self, iaxis):
        '''
        :Description: Read the input point number corresponding to the negative hardware limit switch, -1 is invalid.

        :param axis: axis number. type:int

        :Return: Error code, the returned negative limit input port number. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetRevIn(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetRevJog(self, iaxis, iValue):
        '''
        :Description: Set the input point number corresponding to the negative JOG input, -1 is invalid.

        :param axis: axis number. type:int

        :param iValue: The input port number set. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetRevJog(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iValue))
        return ret

    def ZAux_Direct_GetRevJog(self, iaxis):
        '''
        :Description: Read the input point number corresponding to the negative JOG input, -1 is invalid.

        :param axis: axis number. type:int

        :Return:Error code, return input number. type: int32,int

        '''
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetRevJog(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetRsLimit(self, iaxis, fValue):
        '''
        :Description: Set the negative soft limit position. Setting a larger value is considered to cancel the limit.

        :param axis: axis number. type:int

        :param fValue: Negative limit value. type:float

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_SetRsLimit(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetRsLimit(self, iaxis):
        '''
        :Description: Read the negative soft limit position.

        :param axis: axis number. type:int

        :Return: Error code, set limit value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetRsLimit(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetSpeed(self, iaxis, fValue):
        '''
        :Description: Set the axis speed, unit is units/s, and when multi-axis moves, it is used as the speed of interpolation.

        :param axis: axis number. type:int

        :param fValue: The speed value set. type:float

        :Return:Error code. type: int32
        '''

        ret = zauxdll.ZAux_Direct_SetSpeed(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetSpeed(self, iaxis):
        '''
        :Description: Read the axis speed, unit is units/s, and when multi-axis moves, it is used as the speed of interpolation motion.

        :param axis: axis number. type:int

        :Return: Error code, return speed value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetSpeed(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetSramp(self, iaxis, fValue):
        '''
        :Description: Set S curve settings. 0-Trained acceleration and deceleration.

        :param axis: axis number. type:int

        :param fValue: S curve smoothing time MS. type:float

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_SetSramp(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetSramp(self, iaxis):
        '''
        :Description: Read the S curve settings.

        :param axis: axis number. type:int

        :Return: Error code, smoothing time. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetSramp(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetStartMoveSpeed(self, iaxis, fValue):
        '''
        :Description: Sets the start speed of SP motion for custom speed.

        :param axis: axis number. type:int

        :param fValue: The speed value set. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetStartMoveSpeed(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetStartMoveSpeed(self, iaxis):
        '''
        :Description: Read the start speed of SP motion of the custom speed.

        :param axis: axis number. type:int

        :Return: Error code, the returned SP motion start speed value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetStartMoveSpeed(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetStopAngle(self, iaxis, fValue):
        '''
        :Description: Set the minimum corner to slow down to the lowest arc system.

        :param axis: axis number. type:int

        :param fValue: The angle value set. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetStopAngle(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetStopAngle(self, iaxis):
        '''
        :Description: Take the minimum corner arc system to slow down to the lowest.

        :param axis: axis number. type:int

        :Return:Error code, return corner stop angle. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetStopAngle(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetZsmooth(self, iaxis, fValue):
        '''
        :Description: Set the deceleration chamfer radius.

        :param axis: axis number. type:int

        :param fValue: chamfer radius. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetZsmooth(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetZsmooth(self, iaxis):
        '''
        :Description: Read the chamfer radius.

        :param axis: axis number. type:int

        :Return:Error code, return chamfer radius value. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetZsmooth(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetUnits(self, iaxis, fValue):
        '''
        :Description: Set pulse equivalent.

        :param axis: axis number. type:int

        :param fValue: The equivalent value set. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_SetUnits(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetUnits(self, iaxis):
        '''
        :Description: Read pulse equivalent.

        :param axis: axis number. type:int

        :Return: Error code, the pulse equivalent returned. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetUnits(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetVectorBuffered(self, iaxis):
        '''
        :Description: Read the distance that the current and buffering motion of the return axis has not yet been completed.

        :param axis: axis number. type:int

        :Return:Error code, the remaining distance returned. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetVectorBuffered(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetVpSpeed(self, iaxis):
        '''
        :Description: Read the command speed of the current axis running.

        :param axis: axis number. type:int

        :Return: Error code, the current speed value returned. type: int32,float

        '''
        value = ctypes.c_float()
        ret = zauxdll.ZAux_Direct_GetVpSpeed(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetVariablef(self, pname):
        '''
        :Description: Global variable reading, can also be parameters, etc.

        :param axis: axis number. type:int

        :param pname: Global variable name/or axis parameter name DPOS(0) that specifies the axis number. type:string

        :Return:Error code, return value. type: int32,float

        '''
        _str = pname.encode('utf-8')
        value = (ctypes.c_float)()
        ret = zauxdll.ZAux_Direct_GetVariablef(
            self.handle, _str, ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetVariableInt(self, pname):
        '''
        :Description: Global variable reading, can also be parameters, etc.

        :param axis: axis number. type:int

        :param pname: Global variable name/or axis parameter name DPOS(0) that specifies the axis number. type:string

        :Return:Error code, return value. type: int32,int

        '''
        _str = pname.encode('utf-8')
        value = ctypes.c_int()
        ret = zauxdll.ZAux_Direct_GetVariableInt(
            self.handle, _str, ctypes.byref(value))
        return ret, value

#################The following motion functions support direct calls, not all instructions support it. It must be supported by controller versions in 20130901. ###

    def ZAux_Direct_Base(self, imaxaxises, piAxislist):
        '''
        :Description:BASE instruction call
        Only modify the BASE list of online commands, and do not modify the BASE of the controller's running tasks.
        After modification, all subsequent MOVE and other instructions are based on this BASE.

        :param imaxaxises: Number of participating axes. type:int

        :param piAxislist:Axislist. type:int

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_Base(
            self.handle, ctypes.c_int(imaxaxises), Axislistarray)
        return ret

    def ZAux_Direct_Defpos(self, iaxis, pfDpos):
        '''
        :Description: Define DPOS, not recommended to use, you can directly call SETDPOS to achieve the same effect.

        :param axis: axis number. type:int

        :param pfDpos: The coordinate value set. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Defpos(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(pfDpos))
        return ret

    def ZAux_Direct_Move(self, imaxaxises, piAxislist, pfDisancelist):
        '''
        :Description: Multi-axis relative linear interpolation 20130901 later controller versions support.

        :param imaxaxises: Number of participating axes. type:int

        :param piAxislist:Axislist. type:int

        :param pfDisancelist: Distance list. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        pfDisancelisttarray = (
            ctypes.c_int * len(pfDisancelist))(*pfDisancelist)
        ret = zauxdll.ZAux_Direct_Move(
            self.handle, imaxaxises, Axislistarray, pfDisancelisttarray)
        return ret

    def ZAux_Direct_MoveSp(self, imaxaxises, piAxislist, pfDisancelist):
        '''
        :Description: Relative multi-axis linear interpolation SP motion 20130901 later controller versions support.

        :param imaxaxises: Number of participating axes. type:int

        :param piAxislist:Axislist. type:int

        :param pfDisancelist: Distance list. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        pfDisancelisttarray = (
            ctypes.c_int * len(pfDisancelist))(*pfDisancelist)
        ret = zauxdll.ZAux_Direct_Move(
            self.handle, imaxaxises, Axislistarray, pfDisancelisttarray)
        return ret

    def ZAux_Direct_MoveAbs(self, imaxaxises, piAxislist, pfDisancelist):
        '''
        :Description: Absolute multi-axis linear interpolation 20130901 later controller versions support.

        :param imaxaxises: Number of participating axes. type:int

        :param piAxislist:Axislist. type:int

        :param pfDisancelist: Distance list. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        pfDisancelisttarray = (
            ctypes.c_int * len(pfDisancelist))(*pfDisancelist)
        ret = zauxdll.ZAux_Direct_Move(
            self.handle, imaxaxises, Axislistarray, pfDisancelisttarray)
        return ret

    def ZAux_Direct_MoveAbsSp(self, imaxaxises, piAxislist, pfDisancelist):
        '''
        :Description: Absolute multi-axis linear interpolation SP motion 20130901 later controller versions support.

        :param imaxaxises: Number of participating axes. type:int

        :param piAxislist:Axislist. type:int

        :param pfDisancelist: Distance list. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        pfDisancelisttarray = (
            ctypes.c_int * len(pfDisancelist))(*pfDisancelist)
        ret = zauxdll.ZAux_Direct_Move(
            self.handle, imaxaxises, Axislistarray, pfDisancelisttarray)
        return ret

    def ZAux_Direct_MoveModify(self, iaxis, pfDisance):
        '''
        :Description: Modify the end position in motion 20130901 and later controller versions are supported.

        :param axis: axis number. type:int

        :param pfDisance: Absolute distance. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_MoveModify(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(pfDisance))
        return ret

    def ZAux_Direct_MoveCirc(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection):
        '''
        :Description: Relative center fixed arc interpolation motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The first axis motion coordinate. type:float

        :param fend2: The motion coordinates of the second axis. type:float

        :param fcenter1: The center of the first axis motion, opposite to the starting point. type:float

        :param fcenter2: The center of the second axis moving circle, opposite to the starting point. type:float

        :param idirection:0-counterclockwise, 1-clockwise. type:int

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MoveCirc(self.handle, ctypes.c_int(imaxaxises), Axislistarray, ctypes.c_float(fend1),
                                           ctypes.c_float(fend2), ctypes.c_float(
                                               fcenter1), ctypes.c_float(fcenter2),
                                           ctypes.c_int(idirection))
        return ret

    def ZAux_Direct_MoveCircSp(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection):
        '''
        :Description: Relative center fixed arc interpolation motion Interpolation SP motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The first axis motion coordinate. type:float

        :param fend2: The motion coordinates of the second axis. type:float

        :param fcenter1: The center of the first axis motion, opposite to the starting point. type:float

        :param fcenter2: The center of the second axis moving circle, opposite to the starting point. type:float

        :param idirection:0-counterclockwise, 1-clockwise. type:int

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MoveCircSp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                             ctypes.c_float(fend1), ctypes.c_float(
                                                 fend2), ctypes.c_float(fcenter1),
                                             ctypes.c_float(fcenter2), ctypes.c_int(idirection))
        return ret

    def ZAux_Direct_MoveCircAbs(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection):
        '''
        :Description: Absolute center arc interpolation motion 20130901 Later controller versions support it. Unable to draw a complete circle.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The first axis motion coordinate. type:float

        :param fend2: The motion coordinates of the second axis. type:float

        :param fcenter1: The center of the first axis motion, opposite to the starting point. type:float

        :param fcenter2: The center of the second axis moving circle, opposite to the starting point. type:float

        :param idirection:0-counterclockwise, 1-clockwise. type:int

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MoveCircAbs(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                              ctypes.c_float(fend1), ctypes.c_float(
                                                  fend2), ctypes.c_float(fcenter1),
                                              ctypes.c_float(fcenter2), ctypes.c_int(idirection))
        return ret

    def ZAux_Direct_MoveCircAbsSp(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection):
        '''
        :Description: Absolute center arc interpolation motion 20130901 Later controller versions support it. Unable to draw a complete circle.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The first axis motion coordinate. type:float

        :param fend2: The motion coordinates of the second axis. type:float

        :param fcenter1: The center of the first axis motion, opposite to the starting point. type:float

        :param fcenter2: The center of the second axis moving circle, opposite to the starting point. type:float

        :param idirection:0-counterclockwise, 1-clockwise. type:int

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MoveCircAbsSp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                                ctypes.c_float(fend1), ctypes.c_float(
                                                    fend2), ctypes.c_float(fcenter1),
                                                ctypes.c_float(fcenter2), ctypes.c_int(idirection))
        return ret

    def ZAux_Direct_MoveCirc2(self, imaxaxises, piAxislist, fmid1, fmid2, fend1, fend2):
        '''
        :Description: Relative to 3-point fixed arc interpolation motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fmid1: The middle point of the first axis, distance from the starting point. type:float

        :param fmid2: The middle point of the second axis, distance from the starting point. type:float

        :param fend1: The end point of the first axis, distance from the starting point. type:float

        :param fend2: The end point of the second axis, distance from the starting point. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MoveCirc2(self.handle, ctypes.c_int(imaxaxises), Axislistarray, ctypes.c_float(fmid1),
                                            ctypes.c_float(fmid2), ctypes.c_float(fend1), ctypes.c_float(fend2))
        return ret

    def ZAux_Direct_MoveCirc2Abs(self, imaxaxises, piAxislist, fmid1, fmid2, fend1, fend2):
        '''
        :Description: Absolute 3-point fixed arc interpolation motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fmid1: The middle point of the first axis, distance from the starting point. type:float

        :param fmid2: The middle point of the second axis, distance from the starting point. type:float

        :param fend1: The end point of the first axis, distance from the starting point. type:float

        :param fend2: The end point of the second axis, distance from the starting point. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MoveCirc2Abs(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                               ctypes.c_float(fmid1), ctypes.c_float(
                                                   fmid2), ctypes.c_float(fend1),
                                               ctypes.c_float(fend2))
        return ret

    def ZAux_Direct_MoveCirc2Sp(self, imaxaxises, piAxislist, fmid1, fmid2, fend1, fend2):
        '''
        :Description: SP motion relative to 3 points fixed arc interpolation 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fmid1: The middle point of the first axis, distance from the starting point. type:float

        :param fmid2: The middle point of the second axis, distance from the starting point. type:float

        :param fend1: The end point of the first axis, distance from the starting point. type:float

        :param fend2: The end point of the second axis, distance from the starting point. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MoveCirc2Sp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                              ctypes.c_float(fmid1), ctypes.c_float(
                                                  fmid2), ctypes.c_float(fend1),
                                              ctypes.c_float(fend2))
        return ret

    def ZAux_Direct_MoveCirc2AbsSp(self, imaxaxises, piAxislist, fmid1, fmid2, fend1, fend2):
        '''
        :Description: Absolute 3-point fixed arc interpolation SP motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fmid1: The middle point of the first axis, distance from the starting point. type:float

        :param fmid2: The middle point of the second axis, distance from the starting point. type:float

        :param fend1: The end point of the first axis, distance from the starting point. type:float

        :param fend2: The end point of the second axis, distance from the starting point. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MoveCirc2AbsSp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                                 ctypes.c_float(fmid1), ctypes.c_float(
                                                     fmid2), ctypes.c_float(fend1),
                                                 ctypes.c_float(fend2))
        return ret

    def ZAux_Direct_MHelical(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection, fDistance3,
                             imode):
        '''
        :Description: Relative to the 3-axis center spiral interpolation motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The first axis motion coordinate. type:float

        :param fend2: The motion coordinates of the second axis. type:float

        :param fcenter1: The center of the first axis motion, opposite to the starting point. type:float

        :param fcenter2: The center of the second axis moving circle, opposite to the starting point. type:float

        :param idirection: 0-counterclockwise, 1-clockwise. type:int

        :param fDistance3: The third axis motion distance. type:float

        :param imode: The speed calculation of the third axis: 0 (default) The third axis participates in the speed calculation. 1The third axis does not participate in the speed calculation. type:int

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MHelical(self.handle, ctypes.c_int(imaxaxises), Axislistarray, ctypes.c_float(fend1),
                                           ctypes.c_float(fend2), ctypes.c_float(
                                               fcenter1), ctypes.c_float(fcenter2),
                                           ctypes.c_float(idirection), ctypes.c_float(fDistance3), ctypes.c_int(imode))
        return ret

    def ZAux_Direct_MHelicalAbs(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection, fDistance3,
                                imode):
        '''
        :Description: Absolute 3-axis center spiral interpolation motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The first axis motion coordinate. type:float

        :param fend2: The motion coordinates of the second axis. type:float

        :param fcenter1: The center of the first axis motion, opposite to the starting point. type:float

        :param fcenter2: The center of the second axis moving circle, opposite to the starting point. type:float

        :param idirection: 0-counterclockwise, 1-clockwise. type:int

        :param fDistance3: The third axis motion distance. type:float

        :param imode: The speed calculation of the third axis: 0 (default) The third axis participates in the speed calculation. 1The third axis does not participate in the speed calculation. type:int

        :Return:Error code. type: int32
        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MHelicalAbs(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                              ctypes.c_float(fend1), ctypes.c_float(
                                                  fend2), ctypes.c_float(fcenter1),
                                              ctypes.c_float(fcenter2), ctypes.c_float(
                                                  idirection),
                                              ctypes.c_float(fDistance3), ctypes.c_int(imode))
        return ret

    def ZAux_Direct_MHelicalSp(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection, fDistance3,
                               imode):
        '''
        :Description: Relative to 3-axis center spiral interpolation SP motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The first axis motion coordinate. type:float

        :param fend2: The motion coordinates of the second axis. type:float

        :param fcenter1: The center of the first axis motion, opposite to the starting point. type:float

        :param fcenter2: The center of the second axis moving circle, opposite to the starting point. type:float

        :param idirection: 0-counterclockwise, 1-clockwise. type:int

        :param fDistance3: The third axis motion distance. type:float

        :param imode: The speed calculation of the third axis: 0 (default) The third axis participates in the speed calculation. 1The third axis does not participate in the speed calculation. type:int

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MHelicalSp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                             ctypes.c_float(fend1), ctypes.c_float(
                                                 fend2), ctypes.c_float(fcenter1),
                                             ctypes.c_float(fcenter2), ctypes.c_float(
                                                 idirection),
                                             ctypes.c_float(fDistance3), ctypes.c_int(imode))
        return ret

    def ZAux_Direct_MHelicalAbsSp(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection,
                                  fDistance3, imode):
        '''
        :Description: Absolute 3-axis center spiral interpolation motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The first axis motion coordinate. type:float

        :param fend2: The motion coordinates of the second axis. type:float

        :param fcenter1: The center of the first axis motion, opposite to the starting point. type:float

        :param fcenter2: The center of the second axis moving circle, opposite to the starting point. type:float

        :param idirection: 0-counterclockwise, 1-clockwise. type:int

        :param fDistance3: The third axis motion distance. type:float

        :param imode: The speed calculation of the third axis: 0 (default) The third axis participates in the speed calculation. 1The third axis does not participate in the speed calculation. type:int

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MHelicalAbsSp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                                ctypes.c_float(fend1), ctypes.c_float(
                                                    fend2), ctypes.c_float(fcenter1),
                                                ctypes.c_float(fcenter2), ctypes.c_float(
                                                    idirection),
                                                ctypes.c_float(fDistance3), ctypes.c_int(imode))
        return ret

    def ZAux_Direct_MHelical2(self, imaxaxises, piAxislist, fmid1, fmid2, fend1, fend2, fDistance3, imode):
        '''
        :Description: Relative to 3 axis 3 dots and strokes spiral interpolation motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fmid1: The middle point of the first axis. type:float

        :param fmid2: The middle point of the second axis. type:float

        :param fend1: The end point of the first axis. type:float

        :param fend2: The second axis end point. type:float

        :param fDistance3: The third axis motion distance. type:float

        :param imode: The speed calculation of the third axis. type:int

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MHelical2(self.handle, ctypes.c_int(imaxaxises), Axislistarray, ctypes.c_float(fmid1),
                                            ctypes.c_float(fmid2), ctypes.c_float(
                                                fend1), ctypes.c_float(fend2),
                                            ctypes.c_float(fDistance3), ctypes.c_int(imode))
        return ret

    def ZAux_Direct_MHelical2Abs(self, imaxaxises, piAxislist, fmid1, fmid2, fend1, fend2, fDistance3, imode):
        '''
        :Description: Absolute 3 axis 3 dot stroke spiral interpolation motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fmid1: The middle point of the first axis. type:float

        :param fmid2: The middle point of the second axis. type:float

        :param fend1: The end point of the first axis. type:float

        :param fend2: The second axis end point. type:float

        :param fDistance3: The third axis motion end point. type:float

        :param imode: The speed calculation of the third axis. type:int

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MHelical2Abs(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                               ctypes.c_float(fmid1), ctypes.c_float(
                                                   fmid2), ctypes.c_float(fend1),
                                               ctypes.c_float(fend2), ctypes.c_float(fDistance3), ctypes.c_int(imode))
        return ret

    def ZAux_Direct_MHelical2Sp(self, imaxaxises, piAxislist, fmid1, fmid2, fend1, fend2, fDistance3, imode):
        '''
        :Description: Relative to 3 axis 3 dots and strokes spiral interpolation SP motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fmid1: The middle point of the first axis. type:float

        :param fmid2: The middle point of the second axis. type:float

        :param fend1: The end point of the first axis. type:float

        :param fend2: The second axis end point. type:float

        :param fDistance3: The third axis motion distance. type:float

        :param imode: The speed calculation of the third axis. type:int

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MHelical2Sp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                              ctypes.c_float(fmid1), ctypes.c_float(
                                                  fmid2), ctypes.c_float(fend1),
                                              ctypes.c_float(fend2), ctypes.c_float(fDistance3), ctypes.c_int(imode))
        return ret

    def ZAux_Direct_MHelical2AbsSp(self, imaxaxises, piAxislist, fmid1, fmid2, fend1, fend2, fDistance3, imode):
        '''
        :Description: Absolute 3 axis 3 dots and strokes spiral interpolation SP motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fmid1: The middle point of the first axis. type:float

        :param fmid2: The middle point of the second axis. type:float

        :param fend1: The end point of the first axis. type:float

        :param fend2: The second axis end point. type:float

        :param fDistance3: The third axis motion distance. type:float

        :param imode: The speed calculation of the third axis. type:int

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MHelical2AbsSp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                                 ctypes.c_float(fmid1), ctypes.c_float(
                                                     fmid2), ctypes.c_float(fend1),
                                                 ctypes.c_float(fend2), ctypes.c_float(fDistance3), ctypes.c_int(imode))
        return ret

    def ZAux_Direct_MEclipse(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection, fADis, fBDis):
        '''
        :Description: Relative ellipse interpolation 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The motion coordinate of the first axis of the end point, relative to the starting point. type:float

        :param fend2: The motion coordinate of the second axis of the end point, relative to the starting point. type:float

        :param fcenter1: The motion coordinate of the first axis of the center, relative to the starting point. type:float

        :param fcenter2: The motion coordinate of the second axis of the center, relative to the starting point. type:float

        :param idirection: 0-counterclockwise, 1-clockwise. type:int

        :param fADis: The elliptical radius of the first axis, half-major or half-major. type:float

        :param fBDis: The elliptical radius of the second axis, half-major or half-major axis, can be either an arc or a screw when AB is equal. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MEclipse(self.handle, ctypes.c_int(imaxaxises), Axislistarray, ctypes.c_float(fend1),
                                           ctypes.c_float(fend2), ctypes.c_float(
                                               fcenter1), ctypes.c_float(fcenter2),
                                           ctypes.c_int(idirection), ctypes.c_float(fADis), ctypes.c_float(fBDis))
        return ret

    def ZAux_Direct_MEclipseAbs(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection, fADis,
                                fBDis):
        '''
        :Description: Absolute ellipse interpolation 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The motion coordinate of the first axis of the end point, relative to the starting point. type:float

        :param fend2: The motion coordinate of the second axis of the end point, relative to the starting point. type:float

        :param fcenter1: The motion coordinate of the first axis of the center, relative to the starting point. type:float

        :param fcenter2: The motion coordinate of the second axis of the center, relative to the starting point. type:float

        :param idirection: 0-counterclockwise, 1-clockwise. type:int

        :param fADis: The elliptical radius of the first axis, half-major or half-major. type:float

        :param fBDis: The elliptical radius of the second axis, half-major or half-major axis, can be either an arc or a screw when AB is equal. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MEclipseAbs(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                              ctypes.c_float(fend1), ctypes.c_float(
                                                  fend2), ctypes.c_float(fcenter1),
                                              ctypes.c_float(fcenter2), ctypes.c_int(
                                                  idirection), ctypes.c_float(fADis),
                                              ctypes.c_float(fBDis))
        return ret

    def ZAux_Direct_MEclipseSp(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection, fADis,
                               fBDis):
        '''
        :Description: Relative elliptical interpolation SP motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The motion coordinate of the first axis of the end point, relative to the starting point. type:float

        :param fend2: The motion coordinate of the second axis of the end point, relative to the starting point. type:float

        :param fcenter1: The motion coordinate of the first axis of the center, relative to the starting point. type:float

        :param fcenter2: The motion coordinate of the second axis of the center, relative to the starting point. type:float

        :param idirection: 0-counterclockwise, 1-clockwise. type:int

        :param fADis: The elliptical radius of the first axis, half-major or half-major. type:float

        :param fBDis: The elliptical radius of the second axis, half-major or half-major axis, can be either an arc or a screw when AB is equal. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MEclipseSp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                             ctypes.c_float(fend1), ctypes.c_float(
                                                 fend2), ctypes.c_float(fcenter1),
                                             ctypes.c_float(fcenter2), ctypes.c_int(
                                                 idirection), ctypes.c_float(fADis),
                                             ctypes.c_float(fBDis))
        return ret

    def ZAux_Direct_MEclipseAbsSp(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection, fADis,
                                  fBDis):
        '''
        :Description: Absolute ellipse interpolation SP motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The motion coordinate of the first axis of the end point, relative to the starting point. type:float

        :param fend2: The motion coordinate of the second axis of the end point, relative to the starting point. type:float

        :param fcenter1: The motion coordinate of the first axis of the center, relative to the starting point. type:float

        :param fcenter2: The motion coordinate of the second axis of the center, relative to the starting point. type:float

        :param idirection: 0-counterclockwise, 1-clockwise. type:int

        :param fADis: The elliptical radius of the first axis, half-major or half-major. type:float

        :param fBDis: The elliptical radius of the second axis, half-major or half-major axis, can be either an arc or a screw when AB is equal. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MEclipseAbsSp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                                ctypes.c_float(fend1), ctypes.c_float(
                                                    fend2), ctypes.c_float(fcenter1),
                                                ctypes.c_float(fcenter2), ctypes.c_int(
                                                    idirection),
                                                ctypes.c_float(fADis), ctypes.c_float(fBDis))
        return ret

    def ZAux_Direct_MEclipseHelical(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection, fADis,
                                    fBDis, fDistance3):
        '''
        :Description: Relative Ellipse + Helical Interpolation Movement 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The motion coordinate of the first axis of the end point, relative to the starting point. type:float

        :param fend2: The motion coordinate of the second axis of the end point, relative to the starting point. type:float

        :param fcenter1: The motion coordinate of the first axis of the center, relative to the starting point. type:float

        :param fcenter2: The motion coordinate of the second axis of the center, relative to the starting point. type:float

        :param idirection: 0-counterclockwise, 1-clockwise. type:int

        :param fADis: The elliptical radius of the first axis, half-major or half-major. type:float

        :param fBDis: The elliptical radius of the second axis, half-major or half-major axis, can be either an arc or a screw when AB is equal. type:float

        :param fDistance3: The distance of motion of the third axis. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MEclipseHelical(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                                  ctypes.c_float(
                                                      fend1), ctypes.c_float(fend2),
                                                  ctypes.c_float(
                                                      fcenter1), ctypes.c_float(fcenter2),
                                                  ctypes.c_int(
                                                      idirection), ctypes.c_float(fADis),
                                                  ctypes.c_float(fBDis), ctypes.c_float(fDistance3))
        return ret

    def ZAux_Direct_MEclipseHelicalAbs(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection,
                                       fADis, fBDis, fDistance3, ):
        '''
        :Description: Absolute ellipse + spiral interpolation motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The motion coordinate of the first axis of the end point, relative to the starting point. type:float

        :param fend2: The motion coordinate of the second axis of the end point, relative to the starting point. type:float

        :param fcenter1: The motion coordinate of the first axis of the center, relative to the starting point. type:float

        :param fcenter2: The motion coordinate of the second axis of the center, relative to the starting point. type:float

        :param idirection: 0-counterclockwise, 1-clockwise. type:int

        :param fADis: The elliptical radius of the first axis, half-major or half-major. type:float

        :param fBDis: The elliptical radius of the second axis, half-major or half-major axis, can be either an arc or a screw when AB is equal. type:float

        :param fDistance3: The distance of motion of the third axis. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MEclipseHelicalAbs(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                                     ctypes.c_float(
                                                         fend1), ctypes.c_float(fend2),
                                                     ctypes.c_float(
                                                         fcenter1), ctypes.c_float(fcenter2),
                                                     ctypes.c_int(
                                                         idirection), ctypes.c_float(fADis),
                                                     ctypes.c_float(fBDis), ctypes.c_float(fDistance3))
        return ret

    def ZAux_Direct_MEclipseHelicalSp(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection, fADis,
                                      fBDis, fDistance3):
        '''
        :Description: Relative Ellipse + Helical Interpolation SP Movement 20130901 Later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The motion coordinate of the first axis of the end point, relative to the starting point. type:float

        :param fend2: The motion coordinate of the second axis of the end point, relative to the starting point. type:float

        :param fcenter1: The motion coordinate of the first axis of the center, relative to the starting point. type:float

        :param fcenter2: The motion coordinate of the second axis of the center, relative to the starting point. type:float

        :param idirection: 0-counterclockwise, 1-clockwise. type:int

        :param fADis: The elliptical radius of the first axis, half-major or half-major. type:float

        :param fBDis: The elliptical radius of the second axis, half-major or half-major axis, can be either an arc or a screw when AB is equal. type:float

        :param fDistance3: The distance of motion of the third axis. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MEclipseHelicalSp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                                    ctypes.c_float(
                                                        fend1), ctypes.c_float(fend2),
                                                    ctypes.c_float(
                                                        fcenter1), ctypes.c_float(fcenter2),
                                                    ctypes.c_int(
                                                        idirection), ctypes.c_float(fADis),
                                                    ctypes.c_float(fBDis), ctypes.c_float(fDistance3))
        return ret

    def ZAux_Direct_MEclipseHelicalAbsSp(self, imaxaxises, piAxislist, fend1, fend2, fcenter1, fcenter2, idirection,
                                         fADis, fBDis, fDistance3):
        '''
        :Description: Absolute ellipse + Helical Interpolation SP Movement 20130901 Later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The motion coordinate of the first axis of the end point, relative to the starting point. type:float

        :param fend2: The motion coordinate of the second axis of the end point, relative to the starting point. type:float

        :param fcenter1: The motion coordinate of the first axis of the center, relative to the starting point. type:float

        :param fcenter2: The motion coordinate of the second axis of the center, relative to the starting point. type:float

        :param idirection: 0-counterclockwise, 1-clockwise. type:int

        :param fADis: The elliptical radius of the first axis, half-major or half-major. type:float

        :param fBDis: The elliptical radius of the second axis, half-major or half-major axis, can be either an arc or a screw when AB is equal. type:float

        :param fDistance3: The distance of motion of the third axis. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MEclipseHelicalAbsSp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                                       ctypes.c_float(
                                                           fend1), ctypes.c_float(fend2),
                                                       ctypes.c_float(
                                                           fcenter1), ctypes.c_float(fcenter2),
                                                       ctypes.c_int(
                                                           idirection), ctypes.c_float(fADis),
                                                       ctypes.c_float(fBDis), ctypes.c_float(fDistance3))
        return ret

    def ZAux_Direct_MSpherical(self, imaxaxises, piAxislist, fend1, fend2, fend3, fcenter1, fcenter2, fcenter3, imode,
                               fcenter4, fcenter5):
        '''
        :Description:Space arc + spiral interpolation motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The first axis motion distance parameter 1 relative to the starting point. type:float

        :param fend2: The second axis motion distance parameter 1 relative to the starting point. type:float

        :param fend3: The third axis motion distance parameter 1 relative to the starting point. type:float

        :param fcenter1: The first axis motion distance parameter 2 relative to the starting point. type:float

        :param fcenter2: The second axis motion distance parameter 2 relative to the starting point. type:float

        :param fcenter3: The third axis motion distance parameter 2 relative to the starting point. type:float

        :param imode: Specify the meaning of the previous parameters. type:int
        0 The current point, the middle point, and the end point are fixed arcs. The distance parameter 1 is the end point distance, and the distance parameter 2 is the distance between the middle point.
        1 Walk the smallest arc, distance from parameter 1 is the end point distance, and distance from parameter 2 is the center of the circle.
        2 The current point, the middle point, and the end point are fixed circles. The distance parameter 1 is the end point distance, and the distance parameter 2 is the middle point distance.
        3 First walk the smallest arc, then continue walking the complete circle. The distance from parameter 1 is the end point and the distance from parameter 2 is the center.

        :param fcenter4: The fourth axis motion distance parameter. type:float

        :param fcenter5: The 5th axis motion distance parameter. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MSpherical(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                             ctypes.c_float(fend1), ctypes.c_float(
                                                 fend2), ctypes.c_float(fend3),
                                             ctypes.c_float(
                                                 fcenter1), ctypes.c_float(fcenter2),
                                             ctypes.c_float(fcenter3), ctypes.c_int(
                                                 imode), ctypes.c_float(fcenter4),
                                             ctypes.c_float(fcenter5))
        return ret

    def ZAux_Direct_MSphericalSp(self, imaxaxises, piAxislist, fend1, fend2, fend3, fcenter1, fcenter2, fcenter3, imode,
                                 fcenter4, fcenter5):
        '''
        :Description:Space arc + helix Interpolation SP motion 20130901 later controller versions support.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param fend1: The first axis motion distance parameter 1 relative to the starting point. type:float

        :param fend2: The second axis motion distance parameter 1 relative to the starting point. type:float

        :param fend3: The third axis motion distance parameter 1 relative to the starting point. type:float

        :param fcenter1: The first axis motion distance parameter 2 relative to the starting point. type:float

        :param fcenter2: The second axis motion distance parameter 2 relative to the starting point. type:float

        :param fcenter3: The third axis motion distance parameter 2 relative to the starting point. type:float

        :param imode: Specify the meaning of the previous parameters. type:int
        0 The current point, the middle point, and the end point are fixed arcs. The distance parameter 1 is the end point distance, and the distance parameter 2 is the distance between the middle point.
        1 Walk the smallest arc, distance from parameter 1 is the end point distance, and distance from parameter 2 is the center of the circle.
        2 The current point, the middle point, and the end point are fixed circles. The distance parameter 1 is the end point distance, and the distance parameter 2 is the middle point distance.
        3 First walk the smallest arc, then continue walking the complete circle. The distance from parameter 1 is the end point and the distance from parameter 2 is the center.

        :param fcenter4: The fourth axis motion distance parameter. type:float

        :param fcenter5: The 5th axis motion distance parameter. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MSphericalSp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                               ctypes.c_float(fend1), ctypes.c_float(
                                                   fend2), ctypes.c_float(fend3),
                                               ctypes.c_float(
                                                   fcenter1), ctypes.c_float(fcenter2),
                                               ctypes.c_float(fcenter3), ctypes.c_int(
                                                   imode), ctypes.c_float(fcenter4),
                                               ctypes.c_float(fcenter5))
        return ret

    def ZAux_Direct_MoveSpiral(self, imaxaxises, piAxislist, centre1, centre2, circles, pitch, distance3, distance4):
        '''
        :Description: Involute arc interpolation motion, relative movement mode, starting from an angle 0 when the starting radius is 0 directly diffused.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param centre1: The relative distance of the center of the first axis. type:float

        :param centre2: The relative distance of the center of the second axis. type:float

        :param circles: The number of turns to be rotated can be decimal turns, and negative numbers represent clockwise. type:float

        :param pitch: The diffusion distance of each loop can be negative. type:float

        :param distance3: The function of the 3rd axis spiral, specifying the relative distance of the 3rd axis, this axis does not participate in the speed calculation. type:float

        :param distance4: The function of the 4th axis spiral, specifying the relative distance of the 4th axis, this axis does not participate in the speed calculation. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MoveSpiral(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                             ctypes.c_float(centre1), ctypes.c_float(
                                                 centre2), ctypes.c_float(circles),
                                             ctypes.c_float(
                                                 pitch), ctypes.c_float(distance3),
                                             ctypes.c_float(distance4))
        return ret

    def ZAux_Direct_MoveSpiralSp(self, imaxaxises, piAxislist, centre1, centre2, circles, pitch, distance3, distance4):
        '''
        :Description: Involute arc interpolation SP motion, relative movement mode, starts from an angle 0 when the starting radius is directly diffused.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param centre1: The relative distance of the center of the first axis. type:float

        :param centre2: The relative distance of the center of the second axis. type:float

        :param circles: The number of turns to be rotated can be decimal turns, and negative numbers represent clockwise. type:float

        :param pitch: The diffusion distance of each loop can be negative. type:float

        :param distance3: The function of the 3rd axis spiral, specifying the relative distance of the 3rd axis, this axis does not participate in the speed calculation. type:float

        :param distance4: The function of the 4th axis spiral, specifying the relative distance of the 4th axis, this axis does not participate in the speed calculation. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MoveSpiralSp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                               ctypes.c_float(
                                                   centre1), ctypes.c_float(centre2),
                                               ctypes.c_float(
                                                   circles), ctypes.c_float(pitch),
                                               ctypes.c_float(distance3), ctypes.c_float(distance4))
        return ret

    def ZAux_Direct_MoveSmooth(self, imaxaxises, piAxislist, end1, end2, end3, next1, next2, next3, radius):
        '''
        :Description: Space linear motion, automatically insert the arc at the corner according to the absolute coordinates of the next linear motion. After adding the arc, the end point of the motion will be inconsistent with the end point of the straight line. When the corner is too large, the arc will not be inserted, and when the distance is not enough The radius will be automatically reduced.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param end1: absolute coordinates of the first axis motion. type:float

        :param end2: absolute coordinates of the second axis motion. type:float

        :param end3: absolute coordinates of the third axis motion. type:float

        :param next1: The absolute coordinates of the next linear motion of the first axis. type:float

        :param next2: Absolute coordinates of the next linear motion of the second axis. type:float

        :param next3: Absolute coordinates of the next linear motion of the third axis. type:float

        :param radius: The radius of the insertion arc will automatically shrink when it is too large. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MoveSmooth(self.handle, ctypes.c_int(imaxaxises), Axislistarray, ctypes.c_float(end1),
                                             ctypes.c_float(end2), ctypes.c_float(
                                                 end3), ctypes.c_float(next1),
                                             ctypes.c_float(next2), ctypes.c_float(next3), ctypes.c_float(radius))
        return ret

    def ZAux_Direct_MoveSmoothSp(self, imaxaxises, piAxislist, end1, end2, end3, next1, next2, next3, radius):
        '''
        :Description: Space linear interpolation SP motion, automatically insert the arc at the corner according to the absolute coordinates of the next linear motion. After adding the arc, the end point of the movement will be inconsistent with the end point of the straight line. When the corner is too large, the arc will not be inserted. The radius will be automatically reduced when the distance is not enough.

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param end1: absolute coordinates of the first axis motion. type:float

        :param end2: absolute coordinates of the second axis motion. type:float

        :param end3: absolute coordinates of the third axis motion. type:float

        :param next1: The absolute coordinates of the next linear motion of the first axis. type:float

        :param next2: Absolute coordinates of the next linear motion of the second axis. type:float

        :param next3: Absolute coordinates of the next linear motion of the third axis. type:float

        :param radius: The radius of the insertion arc will automatically shrink when it is too large. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_MoveSmoothSp(self.handle, ctypes.c_int(imaxaxises), Axislistarray,
                                               ctypes.c_float(end1), ctypes.c_float(
                                                   end2), ctypes.c_float(end3),
                                               ctypes.c_float(next1), ctypes.c_float(
                                                   next2), ctypes.c_float(next3),
                                               ctypes.c_float(radius))
        return ret

    def ZAux_Direct_MovePause(self, iaxis, imode):
        '''
        :Description: Motion pause, interpolation motion pauses the spindle. Axis List Axis The first axis.

        :param axis: axis number. type:int

        :param imode:mode type:int
        0 (default) Pauses the current motion.
        1 Pause when the current movement is ready to execute the next movement command after it is completed.
        2 When the current movement is completed and the next movement instruction is about to be executed, and the MARK logo of the two instructions is different, paused. This mode can be used when an action is implemented by multiple instructions, and can be paused after the entire action is completed.

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_MovePause(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(imode))
        return ret

    def ZAux_Direct_MoveResume(self, iaxis):
        '''
        :Description: Cancel the motion pause.

        :param axis: axis number. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_MoveResume(self.handle, ctypes.c_int(iaxis))
        return ret

    def ZAux_Direct_MoveLimit(self, iaxis, limitspeed):
        '''
        :Description: Add speed limit at the end of the current motion to force corner deceleration.

        :param axis: axis number. type:int

        :param limitspeed: limited to speed type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_MoveLimit(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(limitspeed))
        return ret

    def ZAux_Direct_MoveOp(self, iaxis, ioutnum, ivalue):
        '''
        :Description: Add output instructions to the motion buffer.

        :param axis: axis number. type:int

        :param ioutnum: output port number type:int

        :param ivalue: Output port status type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_MoveOp(self.handle, ctypes.c_int(
            iaxis), ctypes.c_int(ioutnum), ctypes.c_int(ivalue))
        return ret

    def ZAux_Direct_MoveOpMulti(self, iaxis, ioutnumfirst, ioutnumend, ivalue):
        '''
        :Description: Add continuous output port output command to the motion buffer.

        :param axis: axis number. type:int

        :param ioutnumfirst: output port start number type:int

        :param ioutnumend: output port end number type:int

        :param ivalue: corresponding output port status binary combination value type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_MoveOpMulti(self.handle, ctypes.c_int(iaxis), ctypes.c_int(ioutnumfirst),
                                              ctypes.c_int(ioutnumend), ctypes.c_int(ivalue))
        return ret

    def ZAux_Direct_MoveOp2(self, iaxis, ioutnum, ivalue, iofftimems):
        '''
        :Description: Add output instructions to the motion buffer, and the output state is flipped after the specified time.

        :param axis: axis number. type:int

        :param ioutnum: output port start number type:int

        :param ivalue: Output port status type:int

        :param iofftimems:State inversion time type:int

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_MoveOp2(self.handle, ctypes.c_int(iaxis), ctypes.c_int(ioutnum), ctypes.c_int(ivalue),
                                          ctypes.c_int(iofftimems))
        return ret

    def ZAux_Direct_MoveAout(self, iaxis, ioutnum, fvalue):
        '''
        :Description: Add output instructions to the motion buffer, and the output state is flipped after the specified time.

        :param axis: axis number. type:int

        :param ioutnum: output port start number type:int

        :param ivalue: Output port status type:int

        :param iofftimems:State inversion time type:int

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_MoveAout(self.handle, ctypes.c_int(iaxis), ctypes.c_int(ioutnum),
                                           ctypes.c_int(fvalue))
        return ret

    def ZAux_Direct_MoveDelay(self, iaxis, itimems):
        '''
        :Description: Add delay command to the motion buffer.

        :param axis: axis number. type:int

        :param ittimems: Delay time ittimems milliseconds. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_MoveDelay(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(itimems))
        return ret

    def ZAux_Direct_MoveTurnabs(self, tablenum, imaxaxises, piAxislist, pfDisancelist):
        '''
        :Description: Rotating table linear interpolation motion. 20130901 later controller versions are supported.

        :param axis: axis number. type:int

        :param tablenum: The table number that stores the rotation table parameters. type:int

        :param imaxaxises: The total number of participating motion axes. type:int

        :param piAxislist: Axis list. type:int

        :param pfDisancelist: Distance list. type:float

        :Return:Error code. type: int32

        '''
        piAxislistarry = (ctypes.c_float * len(piAxislist))(*piAxislist)
        pfDisancelistarry = (
            ctypes.c_float * len(pfDisancelist))(*pfDisancelist)
        ret = zauxdll.ZAux_Direct_MoveTurnabs(self.handle, ctypes.c_int(tablenum), ctypes.c_int(imaxaxises),
                                              piAxislistarry, pfDisancelistarry)
        return ret

    def ZAux_Direct_McircTurnabs(self, tablenum, refpos1, refpos2, mode, end1, end2, imaxaxises, piAxislist,
                                 pfDisancelist):
        '''
        :Description: Rotating table arc + spiral interpolation motion. 20130901 later controller versions are supported.

        :param axis: axis number. type:int

        :param tablenum: The table number that stores the rotation table parameters. type:int

        :param refpos1: The first axis reference point, absolute position. type:float

        :param refpos2: The first axis reference point, absolute position. type:float

        :param mode: 1-The reference point is before the current point, 2-The reference point is behind the end point, 3-The reference point is in the middle, and the three-point circle is used. type:int

        :param end1: The end point of the first axis, absolute position. type:float

        :param end2: The second axis end point, absolute position. type:float

        :param imaxaxises: Number of participating motion axes. type:int

        :param piAxislist:Axislist. type:int

        :param pfDisancelist: Helical axis distance list. type:float

        :Return:Error code. type: int32

        '''
        piAxislistarry = (ctypes.c_float * len(piAxislist))(*piAxislist)
        pfDisancelistarry = (
            ctypes.c_float * len(pfDisancelist))(*pfDisancelist)
        ret = zauxdll.ZAux_Direct_McircTurnabs(self.handle, tablenum, refpos1, refpos2, mode, end1, end2, imaxaxises,
                                               piAxislistarry, pfDisancelistarry)
        return ret

    def ZAux_Direct_Cam(self, iaxis, istartpoint, iendpoint, ftablemulti, fDistance):
        '''
        :Description:Electronic cam Synchronous motion.

        :param axis: axis number. type:int

        :param isstartpoint: The starting point TABLE number. type:int

        :param iendpoint: End point TABLE number. type:int

        :param ftablemulti: Position ratio, generally set to pulse equivalent value. type:float

        :param fDistance: The distance of the reference motion is used to calculate the total motion time. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Cam(self.handle, ctypes.c_int(iaxis), ctypes.c_int(istartpoint),
                                      ctypes.c_int(iendpoint), ctypes.c_float(ftablemulti), ctypes.c_float(fDistance))
        return ret

    def ZAux_Direct_Cambox(self, iaxis, istartpoint, iendpoint, ftablemulti, fDistance, ilinkaxis, ioption,
                           flinkstartpos):
        '''
        :Description:Electronic cam Synchronous motion.

        :param axis: axis number. type:int

        :param isstartpoint: The starting point TABLE number. type:int

        :param iendpoint: End point TABLE number. type:int

        :param ftablemulti: Position ratio, generally set to pulse equivalent value. type:float

        :param fDistance: The distance of the reference motion is used to calculate the total motion time. type:float

        :param eilkaxis:Reference spindle. type:int

        :param ioption: The connection method of the reference axis. type:int

        :param flinkstartpos:ioption condition distance parameter. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Cambox(self.handle, ctypes.c_int(iaxis), ctypes.c_int(istartpoint),
                                         ctypes.c_int(iendpoint), ctypes.c_float(
                                             ftablemulti),
                                         ctypes.c_float(fDistance), ctypes.c_int(
                                             ilinkaxis), ctypes.c_int(ioption),
                                         ctypes.c_float(flinkstartpos))
        return ret

    def ZAux_Direct_Movelink(self, iaxis, fDistance, fLinkDis, fLinkAcc, fLinkDec, iLinkaxis, ioption, flinkstartpos):
        '''
        :Description:Electronic cam Synchronous motion.

        :param axis: The axis number (follow the axis) participating in the movement. type:int

        :param fDistance: The synchronization process follows the axis motion distance. type:float

        :param fLinkDis: The absolute distance of motion of the reference axis (spindle) of the synchronization process. type:float

        :param fLinkAcc: The absolute distance of the reference axis movement following the axis acceleration phase. type:float

        :param fLinkDec: The absolute distance of the reference axis movement following the axis deceleration stage. type:float

        :param iLinkaxis: The axis number of the reference axis. type:int

        :param ioption:Connection mode option. type:int

        :param flinkstartpos: Motion distance in the connection mode option. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Movelink(self.handle, ctypes.c_int(iaxis), ctypes.c_float(fDistance),
                                           ctypes.c_float(fLinkDis), ctypes.c_float(
                                               fLinkAcc), ctypes.c_float(fLinkDec),
                                           ctypes.c_int(
                                               iLinkaxis), ctypes.c_float(ioption),
                                           ctypes.c_float(flinkstartpos))
        return ret

    def ZAux_Direct_Moveslink(self, iaxis, fDistance, fLinkDis, startsp, endsp, iLinkaxis, ioption, flinkstartpos):
        '''
        :Description:Special Cam Synchronous motion.

        :param axis: The axis number (follow the axis) participating in the movement. type:int

        :param fDistance: The synchronization process follows the axis motion distance. type:float

        :param fLinkDis: The absolute distance of motion of the reference axis (spindle) of the synchronization process. type:float

        :param fLinkAcc: The velocity ratio of the following axis and reference axis at startup, units/units units, and negative numbers represent the negative movement of the axis. type:float

        :param fLinkDec: The velocity ratio of the following axis and reference axis at the end, units/units units, negative numbers represent negative movements following the axis. type:float

        :param iLinkaxis: The axis number of the reference axis. type:int

        :param ioption:Connection mode option. type:int

        :param flinkstartpos: Motion distance in the connection mode option. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Moveslink(self.handle, ctypes.c_int(iaxis), ctypes.c_float(fDistance),
                                            ctypes.c_float(fLinkDis), ctypes.c_float(
                                                startsp), ctypes.c_float(endsp),
                                            ctypes.c_int(
                                                iLinkaxis), ctypes.c_int(ioption),
                                            ctypes.c_float(flinkstartpos))
        return ret

    def ZAux_Direct_Connect(self, ratio, link_axis, move_axis):
        '''
        :Description:Connect Synchronous Motion Command Electronic Gear.

        :param ratio: The ratio can be positive or negative, note that it is the ratio of the number of pulses. type:flot

        :param link_axis: The axis number of the connecting axis, the encoder axis is the handwheel. type:int

        :param move_axis: Following axis number. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Connect(self.handle, ctypes.c_float(ratio), ctypes.c_int(link_axis),
                                          ctypes.c_int(move_axis))
        return ret

    def ZAux_Direct_Connpath(self, ratio, link_axis, move_axis):
        '''
        :Description:Connection Synchronous Motion Command Electronic Gear Connect the target position of the current axis to the interpolation vector length of the link_axis axis through the electronic gear.

        :param ratio: The ratio can be positive or negative, note that it is the ratio of the number of pulses. type:int

        :param link_axis: The axis number of the connecting axis, the encoder axis is the handwheel. type:int

        :param move_axis: Following axis number. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Connpath(self.handle, ctypes.c_float(ratio), ctypes.c_int(link_axis),
                                           ctypes.c_int(move_axis))
        return ret

    def ZAux_Direct_Regist(self, iaxis, imode):
        '''
        :Description:Connection Synchronous Motion Command Electronic Gear Connect the target position of the current axis to the interpolation vector length of the link_axis axis through the electronic gear.

        :param axis: axis number. type:int

        :param imode: latch mode. type:int

        :Return:Error code. type: int32: int32

        '''

        ret = zauxdll.ZAux_Direct_Regist(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(imode))
        return ret

    def ZAux_Direct_EncoderRatio(self, iaxis, output_count, input_count):
        '''
        :Description: Encoder input gear ratio, default (1,1).

        :param axis: axis number. type:int

        :param output_count: molecule, do not exceed 65535. type:int

        :param input_count: The denominator, do not exceed 65535. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_EncoderRatio(self.handle, ctypes.c_int(iaxis), ctypes.c_int(output_count),
                                               ctypes.c_int(input_count))
        return ret

    def ZAux_Direct_StepRatio(self, iaxis, output_count, input_count):
        '''
        :Description: Set the step output gear ratio, default (1,1).

        :param axis: axis number. type:int

        :param output_count:molecule,1-65535. type:int

        :param input_count: denominator, 1-65535. type:int

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_StepRatio(self.handle, ctypes.c_int(iaxis), ctypes.c_int(output_count),
                                            ctypes.c_int(input_count))
        return ret

    def ZAux_Direct_Rapidstop(self, imode):
        '''
        :Description: All axes stop immediately.

        :param imode: Stop mode. type:int
        0 (default) Cancel the current motion
        1 Cancel buffering motion
        2 Cancel the current motion and buffering motion.
        3 Immediately interrupt the pulse transmission.

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Rapidstop(self.handle, ctypes.c_int(imode))
        return ret

    def ZAux_Direct_CancelAxisList(self, imaxaxises, piAxislist, imode):
        '''
        :Description: Multiple axes motion stop.

        :param imaxaxises: Number of axes. type:int

        :param piAxislist:Axislist. type:int

        :param imode: Stop mode. type:int
        0 (default) Cancel the current motion
        1 Cancel buffering motion
        2 Cancel the current motion and buffering motion.
        3 Immediately interrupt the pulse transmission.

        :Return:Error code. type: int32

        '''
        Axisarry = (ctypes.c_int * len(piAxislist))(*piAxislist)
        ret = zauxdll.ZAux_Direct_CancelAxisList(
            self.handle, ctypes.c_int(imaxaxises), Axisarry, ctypes.c_int(imode))
        return ret

    def ZAux_Direct_Connframe(self, Jogmaxaxises, JogAxislist, frame, tablenum, Virmaxaxises, VirAxislist):
        '''
        :Description:CONNFRAME robotic reverse solution command supports 2 series and above controllers.
        
        :param Jogmaxaxises: Number of joint axes. type:int

        :param JogAxislist: Joint axis list. type:int

        :param frame: robot type. type:int

        :param tablenum: robot parameter TABLE start number. type:int

        :param Virmaxaxises: The number of virtual axes associated. type:int

        :param VirAxislist: Virtual axis list. type:int

        :Return:Error code. type: int32

        '''
        JogAxislistarry = (ctypes.c_int * len(JogAxislist))(*JogAxislist)
        VirAxislistarry = (ctypes.c_int * len(VirAxislist))(*VirAxislist)
        ret = zauxdll.ZAux_Direct_Connframe(self.handle, ctypes.c_int(Jogmaxaxises), JogAxislistarry,
                                            ctypes.c_int(frame), ctypes.c_int(
                                                tablenum), ctypes.c_int(Virmaxaxises),
                                            VirAxislistarry)
        return ret

    def ZAux_Direct_Connreframe(self, Virmaxaxises, VirAxislist, frame, tablenum, Jogmaxaxises, JogAxislist):
        '''
        :Description:CONNREFRAME robotic manipulator correct command supports 2 series and above controllers.

        :param Virmaxaxises: The number of virtual axes associated. type:int

        :param VirAxislist: Virtual axis list. type:int

        :param frame: robot type. type:int

        :param tablenum: robot parameter TABLE start number. type:int

        :param Jogmaxaxises: Number of joint axes. type:int

        :param JogAxislist: Joint axis list. type:int

        :Return:Error code. type: int32

        '''
        JogAxislistarry = (ctypes.c_int * len(JogAxislist))(*JogAxislist)
        VirAxislistarry = (ctypes.c_int * len(VirAxislist))(*VirAxislist)
        ret = zauxdll.ZAux_Direct_Connreframe(self.handle, Virmaxaxises, VirAxislistarry, frame, tablenum, Jogmaxaxises,
                                              JogAxislistarry)
        return ret

    def ZAux_Direct_Single_Addax(self, iaxis, iaddaxis):
        '''
        :Description: Axis superposition motion is superimposed on the axis axis, and the ADDAX command superimposed on the number of pulses.

        :param axis: superimposed axes type:int

        :param iaddaxis: overlay axis. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Single_Addax(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(iaddaxis))
        return ret

    def ZAux_Direct_Single_Cancel(self, iaxis, imode):
        '''
        :Description: Single-axis motion stop

        :param axis: axis number. type:int

        :param imode: Stop mode. type:int
        0 (default) Cancel the current motion
        1 Cancel buffering motion
        2 Cancel the current motion and buffering motion.
        3 Immediately interrupt the pulse transmission.

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Single_Cancel(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(imode))
        return ret

    def ZAux_Direct_Single_Vmove(self, iaxis, idir):
        '''
        :Description: Single-axis continuous motion.

        :param axis: axis number. type:int

        :param idir: Direction 1 positive -1 negative. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Single_Vmove(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(idir))
        return ret

    def ZAux_Direct_Single_Datum(self, iaxis, imode):
        '''
        :Description: Controller mode returns to zero.

        :param axis: axis number. type:int

        :param imode: mode. type:int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Single_Datum(
            self.handle, ctypes.c_int(iaxis), ctypes.c_int(imode))
        return ret

    def ZAux_Direct_GetHomeStatus(self, iaxis):
        '''
        :Description: Return to zero completion status.

        :param axis: axis number. type:int

        :Return,:Error code, return to zero completion flag 0-Return to zero exception 1 return to zero successful. type: int32,uint32nt32

        '''
        value = (ctypes.c_int)()
        ret = zauxdll.ZAux_Direct_GetHomeStatus(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_Single_Move(self, iaxis, fdistance):
        '''
        :Description: Uniaxial relative motion.

        :param axis: axis number. type:int

        :param fdistance:distance. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Single_Move(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fdistance))
        return ret

    def ZAux_Direct_Single_MoveAbs(self, iaxis, fdistance):
        '''
        :Description: Uniaxial absolute motion.

        :param axis: axis number. type:int

        :param fdistance:distance. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Single_MoveAbs(
            self.handle, ctypes.c_int(iaxis), ctypes.c_float(fdistance))
        return ret

    def ZAux_Direct_SetVrf(self, vrstartnum, numes, pfValue):
        '''
        :Description: Write VR.

        :param vrstartnum:VR start number. type:int

        :param numes: the number of writes. type:int

        :param pfValue: List of data written. type:float

        :Return:Error code. type: int32

        '''
        pfValuearry = (ctypes.c_float * len(pfValue))(*pfValue)
        ret = zauxdll.ZAux_Direct_SetVrf(self.handle, ctypes.c_int(
            vrstartnum), ctypes.c_int(numes), pfValuearry)
        return ret

    def ZAux_Direct_GetVrf(self, vrstartnum, numes):
        '''
        :Description:VR read, can read multiple times at a time.

        :param vrstartnum:VR start number. type:int

        :param numes: the number of writes. type:int

        :Return: Error code, the returned read value, space must be allocated when there are multiple reads. type: int32,float

        '''
        value = (ctypes.c_float * numes)()
        ret = zauxdll.ZAux_Direct_GetVrf(self.handle, ctypes.c_int(vrstartnum), ctypes.c_int(numes),
                                         ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetVrInt(self, vrstartnum, numes):
        '''
        :Description:VRINT read, version 150401 or above must support VRINT's DIRECTCOMMAND read.

        :param vrstartnum:VR start number. type:int

        :param numes: The number of reads. type:int

        :Return: Error code, the returned read value, space must be allocated when there are multiple reads. type: int32,float

        '''
        value = (ctypes.c_int * numes)()
        ret = zauxdll.ZAux_Direct_GetVrf(self.handle, ctypes.c_int(vrstartnum), ctypes.c_int(numes),
                                         ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetTable(self, tabstart, numes, pfValue):
        '''
        :Description: Write table.

        :param tabstart: The TABLE start number written. type:int

        :param numes: the number of writes. type:int

        :param pfValue: The data value written. type:float

        :Return:Error code. type: int32

        '''
        value = (ctypes.c_float * len(pfValue))(*pfValue)
        ret = zauxdll.ZAux_Direct_SetTable(
            self.handle, ctypes.c_int(tabstart), ctypes.c_int(numes), value)
        return ret

    def ZAux_Direct_GetTable(self, tabstart, numes):
        '''
        :Description:table read, can read multiple times at a time.

        :param tabstart: Read the TABLE start address. type:int

        :param numes: The number of reads. type:int

        :Return: Error code, the returned read value, space must be allocated when there are multiple reads. type: int32,float

        '''
        value = (ctypes.c_float * numes)()
        ret = zauxdll.ZAux_Direct_GetTable(self.handle, ctypes.c_int(tabstart), ctypes.c_int(numes),
                                           ctypes.byref(value))
        return ret, value

    def ZAux_TransStringtoFloat(self, pstringin, inumes):
        '''
        :Description: Convert string to float.

        :param pstringin: String of data. type:sting

        :param inumes: converts the number of data. type:int

        :Return: Error code, converted data. type: int32,float

        '''
        _str = pstringin.encode('utf-8')
        value = (ctypes.c_float * inumes)()
        ret = zauxdll.ZAux_TransStringtoFloat(
            _str, inumes, ctypes.byref(value))
        return ret, value

    def ZAux_TransStringtoInt(self, pstringin, inumes):
        '''
        :Description: Convert string to int.

        :param pstringin: String of data. type:sting

        :param inumes: converts the number of data. type:int

        :Return: Error code, converted data. type: int32,int

        '''
        _str = pstringin.encode('utf-8')
        value = (ctypes.c_int * inumes)()
        ret = zauxdll.ZAux_TransStringtoInt(_str, inumes, ctypes.byref(value))
        return ret, value

    def ZAux_WriteUFile(self, sFilename, pVarlist, inum):
        '''
        :Description: Store the variable list in float format to a file, which is consistent with the USB file format of the controller.

        :param sFilename: The absolute path to the file. type:sting

        :param pVarlist: List of data written. type:float

        :Return:Error code. type: int32

        '''
        _str = sFilename.encode('utf-8')
        value = (ctypes.c_float * len(pVarlist))(*pVarlist)
        ret = zauxdll.ZAux_WriteUFile(
            _str, value, len(pVarlist), ctypes.c_int(inum))
        return ret

    def ZAux_ReadUFile(self, sFilename, inum):
        '''
        :Description: Read the variable list in float format, which is consistent with the controller's USB file format.

        :param sFilename: The absolute path to the file. type:sting

        :Return: Error code, read data list. type: int32,int

        '''
        _str = sFilename.encode('utf-8')
        value = (ctypes.c_float * (inum))()
        ret = zauxdll.ZAux_ReadUFile(_str, ctypes.byref(value))
        return ret, value

    def ZAux_Modbus_Set0x(self, start, inum, pdata):
        '''
        :Description:modbus register operation modbus_bit.

        :param start: Start number. type:uint16

        :param inum:quantity. type:uint16

        :param pdata: Set bit state (list type). type:uint8

        :Return:Error code. type: uint16

        '''
        Axislistarray = (ctypes.c_int * len(pdata))(*pdata)
        ret = zauxdll.ZAux_Modbus_Set0x(self.handle, ctypes.c_uint(
            start), ctypes.c_uint(inum), Axislistarray)
        return ret

    def ZAux_Modbus_Get0x(self, start, inum):
        '''
        :Description:modbus register operation modbus_bit.

        :param start: Start number. type:uint16

        :param inum:quantity. type:uint16

        :Return: Error code, returned bit status, bitwise storage. type: int32,uint8

        '''
        value = (ctypes.c_uint8 * inum)()
        ret = zauxdll.ZAux_Modbus_Get0x(self.handle, ctypes.c_uint(
            start), ctypes.c_uint(inum), ctypes.byref(value))
        return ret, value

    def ZAux_Modbus_Set4x(self, start, inum, pdata):
        '''
        :Description:modbus register operation MODBUS_REG.

        :param start: Start number. type:uint16

        :param inum:quantity. type:uint16

        :param inum: Set the value. type:uint16

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int * len(pdata))(*pdata)
        ret = zauxdll.ZAux_Modbus_Set4x(self.handle, ctypes.c_uint(
            start), ctypes.c_uint(inum), Axislistarray)
        return ret

    def ZAux_Modbus_Get4x(self, start, inum):
        '''
        :Description:modbus register operation MODBUS_REG.

        :param start: Start number. type:uint16

        :param inum:quantity. type:uint16

        :Return: Error code, read REG register value. type: int32,uint16

        '''
        value = (ctypes.c_int16 * inum)()
        ret = zauxdll.ZAux_Modbus_Get4x(self.handle, ctypes.c_uint(
            start), ctypes.c_uint(inum), ctypes.byref(value))
        return ret, value

    def ZAux_Modbus_Get4x_Float(self, start, inum):
        '''
        :Description:Modbus Register Operation MODBUS_IEEE Read. MODBUS_IEEE.

        :param start: Start number. type:uint16

        :param inum:quantity. type:uint16

        :Return: Error code, read REG register value. type: int32,float

        '''
        value = (ctypes.c_float * inum)()
        ret = zauxdll.ZAux_Modbus_Get4x_Float(self.handle, ctypes.c_uint(start), ctypes.c_uint(inum),
                                              ctypes.byref(value))
        return ret, value

    def ZAux_Modbus_Set4x_Float(self, start, inum, pdata):
        '''
        :Description: :modbus register operation. MODBUS_IEEE

        :param start: Start number. type:uint16

        :param inum:quantity. type:uint16

        :param pdata: Data list. type:float

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_float * len(pdata))(*pdata)
        ret = zauxdll.ZAux_Modbus_Set4x_Float(
            self.handle, ctypes.c_uint(start), ctypes.c_int(inum), Axislistarray)
        return ret

    def ZAux_Modbus_Get4x_Long(self, start, inum):
        '''
        :Description: :modbus register operation MODBUS_LONG.

        :param start: Start number. type:uint16

        :param inum:quantity. type:uint16

        :Return: Error code, read REG register value. type: int32, int32

        '''

        value = (ctypes.c_int32 * inum)()
        ret = zauxdll.ZAux_Modbus_Get4x_Long(self.handle, ctypes.c_uint(
            start), ctypes.c_int(inum), ctypes.byref(value))
        return ret, value

    def ZAux_Modbus_Set4x_Long(self, start, inum, pidata):
        '''
        :Description: :modbus register operation MODBUS_LONG.

        :param start: Start number. type:uint16

        :param inum:quantity. type:uint16

        :param inum: Set the value. type:int32

        :Return:Error code. type: int32

        '''
        Axislistarray = (ctypes.c_int32 * len(pidata))(*pidata)
        ret = zauxdll.ZAux_Modbus_Set4x_Long(
            self.handle, ctypes.c_uint(start), ctypes.c_int(inum), Axislistarray)
        return ret

    def ZAux_Modbus_Set4x_String(self, start, inum, pdata):
        '''
        :Description: Set modbus_string.

        :param start:modbus start address. type:uint16

        :param inum:length. type:uint16

        :param pdata: The written string. type:sting

        :Return:Error code. type: int32

        '''
        _str = pdata.encode('utf-8')
        ret = zauxdll.ZAux_Modbus_Set4x_String(
            self.handle, ctypes.c_uint(start), ctypes.c_int(inum), _str)
        return ret

    def ZAux_Modbus_Get4x_String(self, start, inum):
        '''
        :Description: Read modbus_string.

        :param start:modbus start address. type:uint16

        :param inum:length. type:uint16

        :Return:Error code, read the returned string. type: int32,sting

        '''
        value = (ctypes.c_char * inum)()
        ret = zauxdll.ZAux_Modbus_Get4x_String(self.handle, ctypes.c_uint(start), ctypes.c_int(inum),
                                               ctypes.byref(value))
        return ret, value

    def ZAux_FlashWritef(self, uiflashid, uinumes, pfvlue):
        '''
        :Description: Write user flash block, float data.

        :param uiflashid:modbus start address. type:uint16

        :param uinumes: Number of variables. type:int32

        :param pfvlue: Data list. type:float

        :Return:Error code. type: int32, int32

        '''
        Axislistarray = (ctypes.c_float * len(pfvlue))(*pfvlue)
        ret = zauxdll.ZAux_FlashWritef(self.handle, ctypes.c_uint16(
            uiflashid), ctypes.c_int32(uinumes), Axislistarray)
        return ret

    def ZAux_FlashReadf(self, uiflashid, uinumes):
        '''
        :Description: Read user flash block, float data.

        :param uiflashid:flash block number. type:uint16

        :param uinumes: The number of buffer variables. type:int32

        :Return: Error code, the number of variables read. type: int32, int32

        '''
        value = (ctypes.c_float * uinumes)()
        ret = zauxdll.ZAux_FlashReadf(self.handle, ctypes.c_uint16(uiflashid), ctypes.c_int32(uinumes),
                                      ctypes.byref(value))
        return ret, value

    def ZAux_Trigger(self):
        '''
        :Description: Oscilloscope trigger function 150723 firmware versions later support.

        '''
        ret = zauxdll.ZAux_Trigger(self.handle)
        return ret

    def ZAux_Direct_MovePara(self, base_axis, paraname, iaxis, fvalue):
        '''
        :Description: Modify parameters in motion. 20170503 or above firmware supports.

        :param base_axis:Motion axis axis number. type:uint32

        :param paraname: parameter name string. type:sting

        :param iaxis: Modify the axis number of the parameter. type: uint32

        :param fvalue: parameter setting value. type:float

        :Return:Error code. type: int32

        '''
        _str = paraname.encode('utf-8')
        ret = zauxdll.ZAux_Direct_MovePara(self.handle, ctypes.c_uint32(base_axis), _str, ctypes.c_int32(iaxis),
                                           ctypes.c_float(fvalue))
        return ret

    def ZAux_Direct_MovePwm(self, base_axis, pwm_num, pwm_duty, pwm_freq):
        '''
        :Description: Modify PWM 20170503 and above firmware support in motion.

        :param base_axis:Motion axis axis number. type:uint32

        :param pwm_num:PWM port number. type:uint32

        :param pwm_duty: The set duty cycle. type: float

        :param pwm_freq: Set frequency. type:float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_MovePwm(self.handle, ctypes.c_uint32(base_axis), ctypes.c_uint32(pwm_num),
                                          ctypes.c_float(pwm_duty), ctypes.c_float(pwm_freq))
        return ret

    def ZAux_Direct_MoveASynmove(self, base_axis, iaxis, fdist, ifsp):
        '''
        :Description: The movement of other axes is triggered during motion. 20170503 and above firmware supports.

        :param base_axis:Motion axis axis number. type:uint32

        :param iaxis: The triggered axis number. type:uint32

        :param fdist: The distance to trigger the motion. type: float

        :param ifsp: Whether the triggering motion is SP motion. type:uint32

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_MoveASynmove(self.handle, ctypes.c_uint32(base_axis), ctypes.c_uint32(iaxis),
                                               ctypes.c_float(fdist), ctypes.c_int32(ifsp))
        return ret

    def ZAux_Direct_MoveTable(self, base_axis, table_num, fvalue):
        '''
        :Description: Modify TABLE in motion.

        :param base_axis: Interpolate the spindle number. type:uint32

        :param table_num:TABLE number. type:uint32

        :param fvalue: Modify the value. type: float

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_Direct_MoveTable(self.handle, ctypes.c_uint32(base_axis), ctypes.c_uint32(table_num),
                                            ctypes.c_float(fvalue))
        return ret

    def ZAux_Direct_MoveWait(self, base_axis, paraname, inum, Cmp_mode, fvalue):
        '''
        :Description: BASE axis motion buffering adds a variable delay firmware version 150802 or above, or XPLC160405 or above.

        :param base_axis: Interpolate the spindle number. type: uint32

        :param paraname: Parameter name string DPOS MPOS IN AIN VPSPEED MSPEED MODBUS_REG MODBUS_IEEE MODBUS_BIT NVRAM VECT_BUFFED REMAIN . type: string

        :param inum: parameter number or axis number. type: int

        :param Cmp_mode:Comparison condition 1 >= 0= -1<= Invalid for BIT type parameters such as IN. type: int

        :param fvalue:Compare values. type: float

        :Return:Error code. type: int32

        '''
        _str = paraname.encode('utf-8')
        ret = zauxdll.ZAux_Direct_MoveWait(self.handle, ctypes.c_uint32(base_axis), _str, ctypes.c_int(inum),
                                           ctypes.c_int(Cmp_mode), ctypes.c_float(fvalue))
        return ret

    def ZAux_Direct_MoveTask(self, base_axis, tasknum, labelname):
        '''
        :Description: BASE axis motion buffer adds a TASK task. When the task has been started, an error will be reported, but it will not affect the execution of the program.

        :param base_axis: Interpolate the spindle number. type: uint32

        :param tasknum: task number. type: uint32

        :param labelname: Global function name or label in BAS. type: sting

        :Return:Error code. type: int32

        '''
        _str = labelname.encode('utf-8')
        ret = zauxdll.ZAux_Direct_MoveTask(self.handle, ctypes.c_uint32(
            base_axis), ctypes.c_uint32(tasknum), _str)
        return ret

    def ZAux_Direct_Pswitch(self, num, enable, axisnum, outnum, outstate, setpos, resetpos):
        '''
        :Description: Position comparison PSWITCH.

        :param num: Comparator number 0-15. type: int

        :param enable: Comparator enable 0/1. type: int

        :param axisnum: Comparison axis number. type: int

        :param outnum: output port number. type: int

        :param outstate: Output status 0/1. type: int

        :param setpos:Compare the starting position. type: float

        :param resetpos: Output reset position. type: float

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_Pswitch(self.handle, ctypes.c_int(num), ctypes.c_int(enable), ctypes.c_int(axisnum),
                                          ctypes.c_int(outnum), ctypes.c_int(
                                              outstate), ctypes.c_float(setpos),
                                          ctypes.c_float(resetpos))
        return ret

    def ZAux_Direct_HwPswitch(self, Axisnum, Mode, Direction, Reserve, Tablestart, Tableend):
        '''
        :Description: Hardware position comparison output The pulse shaft and encoder shaft of the 4 series products support hardware comparison output.

        :param Axisnum: Compare the output axis number. type: int

        :param Mode: Comparator Operation 1-Start the comparator 2-Stop and delete the unfinished points. type: int

        :param Direction: Comparison direction 0-negative direction 1-positive direction. type: int

        :param Reserve:Reserve. type: int

        :param Tablestart:TABLE Start address. type: int

        :param Tableend:TABLE End address. type: int

        :Return:Error code. type: int32

        '''

        ret = zauxdll.ZAux_Direct_HwPswitch(self.handle, ctypes.c_int(Axisnum), ctypes.c_int(Mode),
                                            ctypes.c_int(Direction), ctypes.c_int(
                                                Reserve), ctypes.c_int(Tablestart),
                                            ctypes.c_int(Tableend))
        return ret

    def ZAux_Direct_GetHwPswitchBuff(self, axisnum):
        '''
        :Description: Hardware position comparison output residual buffer acquisition The pulse axis and encoder axis of the 4 series products support hardware comparison output.

        :param axisnum: Compare the output axis number. type: int

        :Return: Error code, position comparison outputs the remaining buffer number. type: int32,int

        '''
        value = (ctypes.c_int)()
        ret = zauxdll.ZAux_Direct_GetHwPswitchBuff(
            self.handle, ctypes.c_int(axisnum), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_HwTimer(self, mode, cyclonetime, optime, reptimes, opstate, opnum):
        '''
        :Description: Hardware timer is used to restore the level after hardware comparison output for a period of time. 4 series products support.

        :param mode: mode. type: int

        :param cyclecloneme:cycle time us unit. type: int

        :param optime: valid time us unit. type: int

        :param reptimes: Number of repetitions. type: int

        :param opstate: Output default state The output port becomes non-this state and starts timing. type: int

        :param opnum: output port number The port that must be able to compare the output hardware. type: int

        :Return:Error code. type: int32
        '''

        ret = zauxdll.ZAux_Direct_HwTimer(self.handle, ctypes.c_int(mode), ctypes.c_int(cyclonetime),
                                          ctypes.c_int(optime), ctypes.c_int(
                                              reptimes), ctypes.c_int(opstate),
                                          ctypes.c_int(opnum))
        return ret

    def ZAux_Direct_GetAxisStopReason(self, iaxis):
        '''
        :Description: The reason for the reading axis stop.

        :param axis: axis number. type: int

        :Return:Error code, returns the status value, the corresponding bit indicates different status. type: int32,int

        '''
        value = (ctypes.c_int)()
        ret = zauxdll.ZAux_Direct_GetAxisStopReason(
            self.handle, ctypes.c_int(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetAllAxisPara(self, sParam, imaxaxis):
        '''
        :Description: Floating point type reads all axis parameter status.

        :param sParam:Baisc The string name of the syntax parameter. type: sting

        :param imaxaxis: Number of axis. type: int

        :Return:Error code, return status value. type: int32,float

        '''
        _str = sParam.encode('utf-8')
        value = (ctypes.c_float * imaxaxis)()
        ret = zauxdll.ZAux_Direct_GetAllAxisPara(
            self.handle, _str, ctypes.c_int(imaxaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetAllAxisInfo(self, max_axis, idle_status, target_pos_status, feedback_pos_status, axis_status):
        max_axis = ctypes.c_int(max_axis)
        '''
        :Description: Read multiple axis parameters at one time.

        :param max_axis: Number of axis. type: int

        :param idle_status: axis running status. type: int

        :param target_pos_status:axis command coordinates.

        :param feedback_pos_status:axis feedback coordinates.

        :param axis_status:axis status.

        :Return:Error code, return status value. type: int32,float

        '''
        # All required parameters are array pointers, so you need to define the function pointer variable of c outside the function
        # idle_status = ctypes.pointer(ctypes.c_int(idle_status))
        # target_pos_status = ctypes.pointer(ctypes.c_float(target_pos_status))
        # feedback_pos_status = ctypes.pointer(ctypes.c_float(feedback_pos_status))
        # axis_status = ctypes.pointer(ctypes.c_int(axis_status))
        ret = zauxdll.ZAux_Direct_GetAllAxisInfo(self.handle, max_axis, idle_status, target_pos_status,
                                                 feedback_pos_status, axis_status)

    def ZAux_Direct_SetUserArray(self, arrayname, arraystart, numes, pfValue):
        '''
        :Description: Set BASIC custom global array.

        :param arrayname: array name. type: sting

        :param arraystart: Array start element us unit. type: int

        :param numes:number of elements. type: int

        :param pfValue: Set the value. type: float

        :Return:Error code. type: int32

        '''
        _str = arrayname.encode('utf-8')
        ARRYY = (ctypes.c_float * len(pfValue))(*pfValue)
        ret = zauxdll.ZAux_Direct_SetUserArray(
            self.handle, _str, ctypes.c_int(arraystart), ctypes.c_int(numes), ARRYY)
        return ret

    def ZAux_Direct_GetUserArray(self, arrayname, arraystart, numes):
        '''
        :Description: Read Set BASIC Custom Global Array, which can read multiple at once.

        :param arrayname: array name. type: sting

        :param arraystart: Array start element us unit. type: int

        :param numes:number of elements. type: int

        :Return: Error code, space must be allocated when reading multiple values ​​of array elements. type: int32,float

        '''
        _str = arrayname.encode('utf-8')
        value = (ctypes.c_float * numes)()
        ret = zauxdll.ZAux_Direct_GetUserArray(self.handle, _str, ctypes.c_int(arraystart), ctypes.c_int(numes),
                                               ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetUserVar(self, varname, pfValue):
        '''
        :Description: Set custom variables.

        :param varname: variable name string. type: sting

        :param pfValue: variable value. type: float

        :Return:Error code. type: int32

        '''
        _str = varname.encode('utf-8')
        ret = zauxdll.ZAux_Direct_SetUserVar(
            self.handle, _str, ctypes.c_float(pfValue))
        return ret

    def ZAux_Direct_GetUserVar(self, varname):
        '''
        :Description: Read custom global variables.

        :param varname: variable name string. type: sting

        :Return:Error code, variable value. type: int32,float

        '''
        _str = varname.encode('utf-8')
        value = (ctypes.c_float)()
        ret = zauxdll.ZAux_Direct_GetUserVar(
            self.handle, _str, ctypes.byref(value))
        return ret, value

    def ZAux_OpenPci(self, cardnum):
        '''
        :Description: Create a link with the controller.

        :param cardnum:PCI card number. type: uint32

        :Return:Error code. type: int32

        '''
        ret = zauxdll.ZAux_OpenPci(ctypes.c_int(
            cardnum), ctypes.pointer(self.handle))
        return ret

    def ZAux_BusCmd_GetNodeNum(self, slot):
        '''
        :Description: The number of nodes on the card slot is read.

        :param slot: The default slot number is 0. type: int

        :Return:Error code, returns the number of successful scan nodes. type: int32,int

        '''
        value = (ctypes.c_int)()
        ret = zauxdll.ZAux_BusCmd_GetNodeNum(
            self.handle, ctypes.c_int(slot), ctypes.byref(value))
        return ret, value

    def ZAux_BusCmd_GetNodeInfo(self, slot, node, sel):
        '''
        :Description: Read information on the node.

        :param slot: The default slot number is 0. type: int

        :param node:node number 0. type: int

        :param sel: Information number 0-Manufacturer number 1-Equipment number 2-Equipment version 3-Alias ​​10-IN number 11-OUT number . type: int

        :Return:Error code, return information. type: int32,int

        '''
        value = (ctypes.c_int)()
        ret = zauxdll.ZAux_BusCmd_GetNodeInfo(self.handle, ctypes.c_int(slot), ctypes.c_int(node), ctypes.c_int(sel),
                                              ctypes.byref(value))
        return ret, value

    def ZAux_BusCmd_GetNodeStatus(self, slot, node):
        '''
        :Description: Read the node bus status.

        :param slot: The default slot number is 0. type: int

        :param node:node number 0. type: int

        :Return: Error code, bitwise processing bit0-node does bit1-communication status bit2-node status exist. type: int32,int

        '''
        value = (ctypes.c_int)()
        ret = zauxdll.ZAux_BusCmd_GetNodeStatus(self.handle, ctypes.c_int(slot), ctypes.c_int(node),
                                                ctypes.byref(value))
        return ret, value

    def ZAux_BusCmd_SDORead(self, slot, node, index, subindex, aype):
        '''
        :Description: Read node SDO parameter information.

        :param slot: The default slot number is 0. type: uint32

        :param node:node number 0. type: uint32

        :param index: Object dictionary number (note that the function is decimal data) 0. type: uint32

        :param subindex: subnumber (note that the function is decimal data). type: uint32

        :param aype:Data type 1-bool 2-int8 3-int16 4-int32 5-uint8 6-uint16 7-uint32. type: uint32

        :Return:Error code, read data value: int32, int

        '''
        value = (ctypes.c_int)()
        ret = zauxdll.ZAux_BusCmd_SDORead(self.handle, ctypes.c_int(slot), ctypes.c_int(node), ctypes.c_int(index),
                                          ctypes.c_int(subindex), ctypes.c_int(aype), ctypes.byref(value))
        return ret, value

    def ZAux_BusCmd_SDOWrite(self, slot, node, index, subindex, aype, Vvalue):
        '''
        :Description: Write node SDO parameter information.

        :param slot: The default slot number is 0. type: uint32

        :param node:node number 0. type: uint32

        :param index: Object dictionary number (note that the function is decimal data) 0. type:uint32

        :param subindex: subnumber (note that the function is decimal data). type: uint32

        :param aype:Data type 1-bool 2-int8 3-int16 4-int32 5-uint8 6-uint16 7-uint32. type: int

        :param Vvalue: The set data value. type: uint32

        :Return:Error code: int32

        '''
        ret = zauxdll.ZAux_BusCmd_SDOWrite(self.handle, ctypes.c_int(slot), ctypes.c_int(node), ctypes.c_int(index),
                                           ctypes.c_int(subindex), ctypes.c_int(aype), ctypes.c_int(Vvalue))
        return ret

    def ZAux_BusCmd_SDOReadAxis(self, iaxis, index, subindex, aype):
        '''
        :Description: SDO reading via axis number.

        :param axis: axis number. type: uint32

        :param index:Object dictionary number. type: uint32

        :param subindex:Object dictionary subnumber. type: uint32

        :param aype:Data type 1-bool 2-int8 3-int16 4-int32 5-uint8 6-uint16 7-uint32. type: uint32

        :Return:Error code, read data value. int32, int32

        '''
        value = (ctypes.c_int)()
        ret = zauxdll.ZAux_BusCmd_SDOReadAxis(self.handle, ctypes.c_int(iaxis), ctypes.c_int(index),
                                              ctypes.c_int(subindex), ctypes.c_int(aype), ctypes.byref(value))
        return ret, value

    def ZAux_BusCmd_SDOWriteAxis(self, iaxis, index, subindex, aype, Vvalue):
        '''
        :Description: SDO writing via axis number.

        :param axis: axis number. type: uint32

        :param index:Object dictionary number. type: uint32

        :param subindex:Object dictionary subnumber. type: uint32

        :param aype:Data type 1-bool 2-int8 3-int16 4-int32 5-uint8 6-uint16 7-uint32. type: uint32

        :param Vvalue:Object dictionary subnumber. type: uint32

        :Return:Error code. type:int32

        '''
        ret = zauxdll.ZAux_BusCmd_SDOWriteAxis(self.handle, ctypes.c_int(iaxis), ctypes.c_int(index),
                                               ctypes.c_int(subindex), ctypes.c_int(aype), ctypes.c_int(Vvalue))
        return ret

    def ZAux_BusCmd_RtexRead(self, iaxis, ipara):
        '''
        :Description:Rtex reads parameter information.

        :param axis: axis number. type: uint32

        :param ipara: Parameter classification*256 + Parameter number Pr7.11-para = 7*256+11. type: uint32

        :Return:Error code, read data value. type:int32,float

        '''
        value = (ctypes.c_float)()
        ret = zauxdll.ZAux_BusCmd_RtexRead(self.handle, ctypes.c_uint(iaxis), ctypes.c_int32(ipara),
                                           ctypes.byref(value))
        return ret, value

    def ZAux_BusCmd_RtexWrite(self, iaxis, ipara, vvalue):
        '''
        :Description:Rtex writes parameter information.

        :param axis: axis number. type: uint32

        :param ipara: Parameter classification*256 + Parameter number Pr7.11-para = 7*256+11. type: uint32

        :param vvalue: set data value. type: float

        :Return:Error code. type:int32

        '''
        ret = zauxdll.ZAux_BusCmd_RtexWrite(self.handle, ctypes.c_uint(iaxis), ctypes.c_uint(ipara),
                                            ctypes.c_float(vvalue))
        return ret

    def ZAux_BusCmd_SetDatumOffpos(self, iaxis, fValue):
        '''
        :Description: Set the zero offset distance.

        :param axis: axis number. type: uint32

        :param fValue: Offset distance. type: float

        :Return:Error code. type:int32

        '''
        ret = zauxdll.ZAux_BusCmd_SetDatumOffpos(
            self.handle, ctypes.c_uint(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_BusCmd_GetDatumOffpos(self, iaxis):
        '''
        :Description: Read back the zero offset distance.

        :param axis: axis number. type: uint32

        :Return:Error code, offset distance. type:int32,float

        '''
        value = (ctypes.c_float)()
        ret = zauxdll.ZAux_BusCmd_GetDatumOffpos(
            self.handle, ctypes.c_uint(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_BusCmd_Datum(self, iaxis, homemode):
        '''
        :Description: The bus drive returns to zero.

        :param axis: axis number. type: uint32

        :param homemode: Return to zero mode, check the drive manual. type: uint32

        :Return:Error code. type:int32

        '''
        ret = zauxdll.ZAux_BusCmd_Datum(
            self.handle, ctypes.c_uint(iaxis), ctypes.c_uint(homemode))
        return ret

    def ZAux_BusCmd_GetHomeStatus(self, iaxis):
        '''
        :Description: Drive returns to zero and complete state.

        :param axis: axis number. type: uint32

        :Return: Error code, zero completion flag 0-Return to zero exception 1 Return to zero successful. type:int32,uint32

        '''
        value = (ctypes.c_int)()
        ret = zauxdll.ZAux_BusCmd_GetHomeStatus(
            self.handle, ctypes.c_uint(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_BusCmd_DriveClear(self, iaxis, mode):
        '''
        :Description: Set to clear the bus servo alarm.

        :param axis: axis number. type: uint32

        :param mode: Mode 0-Clear the current alarm 1-Clear the historical alarm 2-Clear the external input alarm. type: uint32

        :Return:Error code. type:int32

        '''
        ret = zauxdll.ZAux_BusCmd_DriveClear(
            self.handle, ctypes.c_uint(iaxis), ctypes.c_uint(mode))
        return ret

    def ZAux_BusCmd_GetDriveTorque(self, iaxis):
        '''
        :Description: Read the current torque of the current bus driver. You need to set the corresponding DRIVE_PROFILE type.

        :param axis: axis number. type: int

        :Return: Error code, current torque. type:int32,int

        '''
        value = (ctypes.c_int)()
        ret = zauxdll.ZAux_BusCmd_GetDriveTorque(
            self.handle, ctypes.c_uint(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_BusCmd_SetMaxDriveTorque(self, iaxis, piValue):
        '''
        :Description: Set the current bus driving maximum torque. The corresponding DRIVE_PROFILE type needs to be set.

        :param axis: axis number. type: int

        :param piValue: Maximum torque limit. type: int

        :Return:Error code. type:int32

        '''
        ret = zauxdll.ZAux_BusCmd_SetMaxDriveTorque(
            self.handle, ctypes.c_uint(iaxis), ctypes.c_uint(piValue))
        return ret

    def ZAux_BusCmd_GetMaxDriveTorque(self, iaxis):
        '''
        :Description: Read the current bus driving maximum torque. The corresponding DRIVE_PROFILE type needs to be set.

        :param axis: axis number. type: int

        :Return: Error code, maximum torque returned. type:int32,int

        '''
        value = (ctypes.c_int)()
        ret = zauxdll.ZAux_BusCmd_GetMaxDriveTorque(
            self.handle, ctypes.c_uint(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_Direct_SetDAC(self, iaxis, fValue):
        '''
        :Description: Set the analog output. You can in torque and speed mode. The corresponding DRIVE_PROFILE type and ATYPE are required for bus drivers.

        :param axis: axis number. type: int

        :param piValue: analog output value. type: float

        :Return:Error code. type:int32

        '''
        ret = zauxdll.ZAux_Direct_SetDAC(
            self.handle, ctypes.c_uint(iaxis), ctypes.c_float(fValue))
        return ret

    def ZAux_Direct_GetDAC(self, iaxis):
        '''
        :Description: Read analog output. You can use the torque and speed mode. The corresponding DRIVE_PROFILE type and ATYPE are required to be set.

        :param axis: axis number. type: int

        :Return:Error code, analog quantity return value. type:int32,float
        '''
        value = (ctypes.c_float)()
        ret = zauxdll.ZAux_Direct_GetDAC(
            self.handle, ctypes.c_uint(iaxis), ctypes.byref(value))
        return ret, value

    def ZAux_BusCmd_InitBus(self):
        '''
        :Description:Bus initialization (it is valid for the Zmotion tools tool software to configure the bus parameter controller).

        :Return:Error code. type:int32

        '''
        ret = zauxdll.ZAux_BusCmd_InitBus(self.handle)
        return ret

    def ZAux_BusCmd_GetInitStatus(self):
        '''
        :Description: Get the bus initialization completion status (it is valid for the Zmotion tools tool software to configure the bus parameter controller to use).

        :Return: Error code, 0-Initialization failed 1 Success. type:int32,int

        '''
        value = (ctypes.c_int)()
        ret = zauxdll.ZAux_BusCmd_GetInitStatus(
            self.handle, ctypes.byref(value))
        return ret, value

    def ZAux_Direct_GetInMulti(self, startio, endio):
        '''
        :Description: Read multiple input signals.

        :param startio:IO port start number. type: int

        :param endio:IO port end number. type: int

        :Return: Error code, the status value of the input port obtained by bit. Up to 32 output port statuses are stored. type:int32,int32

        '''
        value = (ctypes.c_int)()
        ret = zauxdll.ZAux_Direct_GetInMulti(self.handle, ctypes.c_uint(startio), ctypes.c_uint(endio),
                                             ctypes.byref(value))
        return ret, value

    def ZAux_SetTimeOut(self, timems):
        '''
        :Description: The delay waiting time of the command.

        :param timesms: Waiting time MS. type: int

        :Return:Error code. type:int32

        '''
        ret = zauxdll.ZAux_SetTimeOut(self.handle, ctypes.c_uint(timems))
        return ret

    def ZAux_Direct_HwPswitch2(self, Axisnum, Mode, Opnum, Opstate, ModePara1, ModePara2, ModePara3, ModePara4):
        '''
        :Description: Hardware position comparison output 2 4 series products, supported by 20170513 or above. ZMC306E/306N supports.

        :param Axisnum: Compare the output axis number. type: int

        :param Mode: Mode   1-Start the comparator. type: int
                            2- Stop and delete unfinished comparison points.
                            3- Vector comparison method.
                            4- Vector comparison method, single comparison point.
                            5- Vector comparison method, periodic pulse mode.
                            6-Vector comparison method, periodic mode, this mode is generally used with HW_TIMER

        :param Opnum: output port number. 4 Series out 0-For hardware position comparison output. type: int

        :param Opstate: The output state of the first comparison point. 0-Close 1-Open. type: int

        :param ModePara1: Multifunctional parameters. type: float

        :param ModePara2: Multifunctional parameters. type: float

        :param ModePara3: Multifunctional parameters. type: float

        :param ModePara4: Multifunctional parameters. type: float
        :Return:Error code. type:int32

        '''
        ret = zauxdll.ZAux_Direct_HwPswitch2(self.handle, ctypes.c_int(Axisnum), ctypes.c_int(Mode),
                                             ctypes.c_int(Opnum), ctypes.c_int(
                                                 Opstate), ctypes.c_float(ModePara1),
                                             ctypes.c_float(
                                                 ModePara2), ctypes.c_float(ModePara3),
                                             ctypes.c_float(ModePara4))
        return ret

    def ZAux_Direct_SetOutMulti(self, iofirst, ioend, istate):
        '''
        :Description:IO Sets the output status of the circuit.

        :param iofirst: IO port start number. type: int

        :param ioend:IO port end number. type: int

        :param isstate:. Output port status, state is set bit by bit, and one UNIT corresponds to 32 output port status (list type). type: int32

        :Return: Error code, output port status. type:int32

        '''
        arry = (ctypes.c_uint32 * len(istate))(*istate)
        ret = zauxdll.ZAux_Direct_SetOutMulti(
            self.handle, ctypes.c_uint(iofirst), ctypes.c_int(ioend), arry)
        return ret

    def ZAux_Direct_GetOutMulti(self, iofirst, ioend):
        '''
        :Description:IO interface obtains the multi-output status.

        :param iofirst: IO port start number. type: int

        :param ioend:IO port end number. type: int

        :Return: Error code, output port status. type:int32

        '''
        value = (ctypes.c_int)()
        ret = zauxdll.ZAux_Direct_GetOutMulti(self.handle, ctypes.c_uint(iofirst), ctypes.c_int(ioend),
                                              ctypes.byref(value))
        return ret, value

    def ZAux_Direct_MultiMove(self, iMoveLen, imaxaxises, piAxislist, pfDisancelist):
        '''
        :Description: Multiple relative multi-axis linear interpolation.

        :param iMoveLen: Fill in the length of movement. type: int

        :param imaxaxises: The total number of participating motion axes. type: int

        :param piAxislist: Axis list. type: int

        :param pfDisancelist: Distance list. type: float

        :Return:Error code. type:int32

        '''
        value = (ctypes.c_int * len(piAxislist))(*piAxislist)
        b = (ctypes.c_float * len(pfDisancelist))(*pfDisancelist)
        ret = zauxdll.ZAux_Direct_MultiMove(
            self.handle, iMoveLen, imaxaxises, value, b)
        return ret

    def ZAux_Direct_MultiMoveAbs(self, iMoveLen, imaxaxises, piAxislist, pfDisancelist):
        '''
        :Description: Multiple absolute multi-axis linear interpolation.

        :param iMoveLen: Fill in the length of movement. type: int

        :param imaxaxises: The total number of participating motion axes. type: int

        :param piAxislist: Axis list. type: int

        :param pfDisancelist: Distance list. type: float

        :Return:Error code. type:int32

        '''
        value = (ctypes.c_int * len(piAxislist))(*piAxislist)
        b = (ctypes.c_float * len(pfDisancelist))(*pfDisancelist)
        ret = zauxdll.ZAux_Direct_MultiMoveAbs(
            self.handle, iMoveLen, imaxaxises, value, b)
        return ret

    def ZAux_Direct_MultiMovePt(self, iMoveLen, imaxaxises, piAxislist, pTickslist, pfDisancelist):
        '''
        :Description: Multiple relative PT motions.

        :param iMoveLen: The number of exercises filled in. type: int

        :param imaxaxises: The total number of participating motion axes. type: int

        :param piAxislist: Axis list. type: int

        :param piAxislist: Periodic list. type: int

        :param pfDisancelist: Distance list. type: float

        :Return:Error code. type:int32

        '''
        value = (ctypes.c_int * len(piAxislist))(*piAxislist)
        b = (ctypes.c_float * len(pfDisancelist))(*pfDisancelist)
        a = (ctypes.c_float * len(pTickslist))(*pTickslist)
        ret = zauxdll.ZAux_Direct_MultiMovePt(
            self.handle, iMoveLen, imaxaxises, value, a, b)
        return ret

    def ZAux_Direct_MultiMovePtAbs(self, iMoveLen, imaxaxises, piAxislist, pTickslist, pfDisancelist):
        '''
        :Description: Multiple absolute PT motions.

        :param iMoveLen: The number of exercises filled in. type: int

        :param imaxaxises: The total number of participating motion axes. type: int

        :param piAxislist: Axis list. type: int

        :param piAxislist: Periodic list. type: int

        :param pfDisancelist: Distance list. type: float

        :Return:Error code. type:int32

        '''
        value = (ctypes.c_int * len(piAxislist))(*piAxislist)
        b = (ctypes.c_float * len(pfDisancelist))(*pfDisancelist)
        a = (ctypes.c_float * len(pTickslist))(*pTickslist)
        ret = zauxdll.ZAux_Direct_MultiMovePtAbs(
            self.handle, iMoveLen, imaxaxises, value, a, b)
        return ret

    def ZAux_ZarDown(self, Filename, run_mode):
        '''
        :Description: Download the ZAR program to the controller to run.

        :param Filename:BAS file name with path. type: sting

        :param run_mode:Download mode 0-RAM 1-ROM. type: int32

        :Return:Error code. type:int32nt32

        '''
        _str = Filename.encode('utf-8')
        ret = zauxdll.ZAux_ZarDown(self.handle, _str, ctypes.c_int32(run_mode))
        return ret

    def ZAux_SetRtcTime(self, RtcDate, RtcTime):
        '''
        :Description: Set the RTC time.

        :param RtcDate: System Date Format YYMMDD. type: sting

        :param RtcTime: System time format HHMMSS. type: sting

        :Return:Error code. type:int32

        '''
        _STR = RtcDate.encode('utf-8')
        _STB = RtcTime.encode('utf-8')
        ret = zauxdll.ZAux_SetRtcTime(self.handle, _STR, _STB)
        return ret

    def ZAux_FastOpen(self, type, pconnectstring, uims):
        '''
        :Description: Establish a link with the controller, and you can specify the waiting time for the connection.

        :param type: Connection type 1-COM 2-ETH 3-Reserved USB 4-PCI. type: int

        :param pconnectstring:Connection string pconnectstring COM slogan/IP address. type: sting

        :param uims:Connection timeout uims. type:int

        :Return:Error code. type:int32

        '''
        ip_bytes = pconnectstring.encode('utf-8')
        ret = zauxdll.ZAux_FastOpen(
            type, ip_bytes, uims, ctypes.pointer(self.handle))
        return ret

    def ZAux_Direct_UserDatum(self, iaxis, imode, HighSpeed, LowSpeed, DatumOffset):
        '''
        :Description: Customize the secondary zero return.

        :param axis: axis number. type: int

        :param imode: Return to zero mode. type: int

        :param HighSpeed: Back to zero high speed. type:float

        :param LowSpeed: Return to zero low speed. type:float

        :param DatumOffset: Secondary return to zero offset distance. type:float

        :Return:Error code. type:int32

        '''
        ret = zauxdll.ZAux_Direct_UserDatum(self.handle, ctypes.c_int(iaxis), ctypes.c_int(imode),
                                            ctypes.c_float(
                                                HighSpeed), ctypes.c_float(LowSpeed),
                                            ctypes.c_float(DatumOffset))
        return ret

    def ZAux_Direct_Pitchset(self, iaxis, iEnable, StartPos, maxpoint, DisOne, TablNum, pfDisancelist):
        '''
        :Description: Set the pitch compensation of the axis, the expansion axis is invalid.

        :param axis: axis number. type: int

        :param iEnable: Whether to enable compensation. type: int

        :param StartPos: Start compensation MPOS position. type:float

        :param maxpoint: Total points in the compensation range. type:uint32

        :param DisOne: Spacing between each compensation point. type:float

        :param TablNum: Fill in the TABLE system array start boot address. type:uint32

        :param pfDisancelist: List of interval compensation values. type:float

        :Return:Error code. type:int32

        '''
        value = (ctypes.c_int * len(pfDisancelist))(*pfDisancelist)
        ret = zauxdll.ZAux_Direct_Pitchset(self.handle, ctypes.c_int(iaxis), ctypes.c_int(iEnable),
                                           ctypes.c_float(StartPos), ctypes.c_int(
                                               maxpoint), ctypes.c_float(DisOne),
                                           ctypes.c_int(TablNum), value)
        return ret

    def ZAux_Direct_Pitchset2(self, iaxis, iEnable, StartPos, maxpoint, DisOne, TablNum, pfDisancelist, RevTablNum,
                              RevpfDisancelist):
        '''
        :Description: Set the pitch of the axis to bidirectional compensation, the expansion axis is invalid.

        :param axis: axis number. type: int

        :param iEnable: Whether to enable compensation. type: int

        :param StartPos: Start compensation MPOS position. type:float

        :param maxpoint: Total points in the compensation range. type:uint32

        :param DisOne: Spacing between each compensation point. type:float

        :param TablNum: Fill in the TABLE system array start boot address. type:uint32

        :param pfDisancelist: List of interval compensation values. type:float

        :param RevTablNum: Fill in the TABLE system array start boot address. type:uint32

        :param RevpfDisancelist: Reverse interval compensation value list The direction of the compensation data is consistent in the forward direction. type:float

        :Return:Error code. type:int32

        '''
        value = (ctypes.c_int * len(pfDisancelist))(*pfDisancelist)
        b = (ctypes.c_int * len(RevpfDisancelist))(*RevpfDisancelist)
        ret = zauxdll.ZAux_Dire

    #
    # itchset2(self.handle, ctypes.c_int(iaxis), ctypes.c_int(iEnable),
    #          ctypes.c_float(StartPos), ctypes.c_int(maxpoint), ctypes.c_float(DisOne),
    #          ctypes.c_int(TablNum), value, ctypes.c_int(RevTablNum), b)
    #     return ret

# ''''''


def ZAux_CycleUpEnable(self, cycleindex, fintervalms, psetesname):
    # '''
    # :Description: Enable period reporting.
    #
    # :param cycleindex: Report channel number, 0-maximum value-1. type: uint32
    #
    # :param finevalms: Report interval time, ms unit, cannot be lower than the controller SERVO_PERIOD. type: int
    #
    # :param psetesname:Report parameter selection, syntax: Parameter 1, Parameter 2 (index), Parameter 3 (index, numes). type:sting
    #
    # :Return:Error code. type:int32
    #
    # '''
    _str = psetesname.encode('utf-8')
    ret = zauxdll.ZAux_CycleUpEnable(self.handle, ctypes.c_int(
        cycleindex), ctypes.c_float(fintervalms), _str)
    return ret


def ZAux_CycleUpDisable(self, cycleindex):
    # '''
    # :Description: De-enable period reporting.
    #
    # :param cycleindex: Report channel number, 0-maximum value-1. type: uint32
    #
    # :Return:Error code. type:int32
    #
    # '''

    ret = zauxdll.ZAux_CycleUpDisable(self.handle, ctypes.c_int(cycleindex))
    return ret


def ZAux_CycleUpGetRecvTimes(self, cycleindex):
    '''
    :Description: The number of packets received periodically exceeds overflow. Debugging and using.

    :param cycleindex: Report channel number, 0-maximum value-1. type: uint32

    :Return:Error code. type:int32

    '''

    ret = zauxdll.ZAux_CycleUpGetRecvTimes(
        self.handle, ctypes.c_int(cycleindex))
    return ret


def ZAux_CycleUpForceOnce(self, cycleindex):
    '''
    :Description: Forced to report once, and call it if the idle may be inaccurate after the movement command.

    :param cycleindex: Report channel number, 0-maximum value-1. type: uint32

    :Return:Error code. type:int32

    '''
    ret = zauxdll.ZAux_CycleUpGetRecvTimes(
        self.handle, ctypes.c_int(cycleindex))
    return ret


def ZAux_CycleUpReadBuff(self, cycleindex, psetname, isetindex):
    '''
    :Description: Read content from the periodic report.

    :param cycleindex: -1, automatically select the cycle number. type: uint32

    :param psetname: parameter name. type:string

    :param isetindex: parameter number. type: uint32

    :Return:Error code, return value. type:int32,double

    '''
    _str = psetname.encode('utf-8')
    value = (ctypes.c_double)()
    ret = zauxdll.ZAux_CycleUpReadBuff(self.handle, ctypes.c_int32(cycleindex), _str, ctypes.c_int32(isetindex),
                                       ctypes.byref(value))
    return ret, value


def ZAux_CycleUpReadBuffInt(self, cycleindex, psetname, isetindex):
    '''
    :Description: Read content from the periodic report.

    :param cycleindex: -1, automatically select the cycle number. type: uint32

    :param psetname: parameter name. type:string

    :param isetindex: parameter number. type: uint32

    :Return:Error code, return value. type:int32,int32

    '''
    _str = psetname.encode('utf-8')
    value = (ctypes.c_int32)()
    ret = zauxdll.ZAux_CycleUpReadBuffInt(self.handle, ctypes.c_int32(cycleindex), _str, ctypes.c_int32(isetindex),
                                          ctypes.byref(value))
    return ret, value


def ZAux_Direct_MultiLineN(self, imode, iMoveLen, imaxaxises, piAxislist, pfDisancelist):
    '''
    :Description: Multi-axis polyline linear interpolation.

    :param imode:bit0- bifabs
                 bit1- bifsp
                 bit2- bifresume
                 bit3- bifmovescan call. type: int

    :param iMoveLen: Fill in the length of movement. type: int

    :param imaxaxises: The total number of participating motion axes. type:int

    :param piAxislist: Axis list. type:uint32

    :param pfDisancelist: Distance list iMoveLen * imaxaxises. type:float

    :Return: Error code, the maximum command length that the remaining buffer can issue. type:int32,int

    '''
    a = (ctypes.c_int * len(piAxislist))(*piAxislist)
    b = (ctypes.c_int * len(pfDisancelist))(*pfDisancelist)
    ret = zauxdll.ZAux_Direct_MultiLineN(self.handle, ctypes.c_int(imode), ctypes.c_int(iMoveLen),
                                         ctypes.c_int(imaxaxises), a, b)
    return ret


def ZAux_Direct_MoveSync(self, imode, synctime, syncposition, syncaxis, imaxaxises, piAxislist, pfDisancelist):
    '''
    :Description: The belt follows movement synchronously.

    :param imode: Synchronous mode -1 End mode -2 Forced end 0-The first axis follows 10-The second axis follows 20-The second axis follows Decimal place -angle: Belt rotation angle type: float

    :param synctime: Fill in the length of movement. type: int

    :param syncposition: Synchronous time, ms unit, this motion is completed within the specified time, and when completed, the BASE axis follows the belt and maintains the same speed. 0 means that the synchronization time is estimated based on the velocity acceleration of the motion axis, which may be inaccurate. type:int

    :param syncaxis: belt shaft shaft number. type:uint32

    :param imaxaxises: Total number of participating in synchronization slave axes. type:int

    :param piAxislist: Slave axis number list. type:int

    :param pfDisancelist: List of absolute coordinate positions of the belt axis when the object is sensed. type:float

    :Return:Error code. type:int32

    '''
    a = (ctypes.c_int * len(piAxislist))(*piAxislist)
    b = (ctypes.c_int * len(pfDisancelist))(*pfDisancelist)
    ret = zauxdll.ZAux_Direct_MoveSync(self.handle, ctypes.c_int(imode), ctypes.c_int(synctime),
                                       ctypes.c_int(syncposition), ctypes.c_int(
                                           syncaxis), ctypes.c_int(imaxaxises),
                                       a, b)
    return ret


def ZAux_Direct_MoveCancel(self, base_axis, Cancel_Axis, iMode):
    '''
    :Description: Cancel other axis movements in the motion buffer to achieve the effect of canceling other axis movements in the motion.

    :param base_axis:Motion axis axis number. type: int32

    :param Cancel_Axis:Stop axis number. type: int32

    :param iMode:Stop mode. type:int
                 0:Cancel the current movement
                 1: Cancel buffering motion
                 2: Cancel the current motion and buffering motion
                 3: Immediately interrupt pulse transmission

    :Return:Error code. type:int32

    '''
    ret = zauxdll.ZAux_Direct_MoveCancel(self.handle, ctypes.c_int(base_axis), ctypes.c_int(Cancel_Axis),
                                         ctypes.c_int(iMode))
    return ret


def ZAux_Direct_CycleRegist(self, iaxis, imode, iTabStart, iTabNum):
    '''
    :Description: Continuous position latch instruction.

    :param axis: axis number. type: int

    :param imode: latch mode. type: int

    :param iTabStart: The table position of the continuously latched content, the first table element stores the number of latches, and the latched coordinates are stored later. 
                      The maximum number of saved = numes-1, and it is written in a loop when overflowing. type:int

    :param iTabNum: The number of tables occupied. type:int

    :Return:Error code. type:int32

    '''
    ret = zauxdll.ZAux_Direct_CycleRegist(self.handle, ctypes.c_int(iaxis), ctypes.c_int(imode),
                                          ctypes.c_int(iTabStart), ctypes.c_int(iTabNum))
    return ret


def ZAux_BusCmd_NodePdoWrite(self, inode, index, subindex, type, vvalue):
    '''
    :Description:Pdo write operation.

    :param inode:node number. type: int32

    :param index:Object dictionary. type: int32

    :param subindex: child object. type:uint32

    :param type: data type. type:uint32

    :param vvalue: Write data value. type:int

    :Return:Error code. type:int32

    '''
    ret = zauxdll.ZAux_BusCmd_NodePdoWrite(self.handle, ctypes.c_int(inode), ctypes.c_int(index),
                                           ctypes.c_int(subindex), ctypes.c_int(type), ctypes.c_int(vvalue))
    return ret


def ZAux_BusCmd_NodePdoRead(self, inode, index, subindex, type):
    '''
    :Description:Pdo read operation.

    :param inode:node number. type: int32

    :param index:Object dictionary. type: int32

    :param subindex: child object. type:uint32

    :param type: data type. type:uint32

    :param vvalue: Write data value. type:int

    :Return:Error code, read data value. type:int32,int

    '''
    value = (ctypes.c_int)()
    ret = zauxdll.ZAux_BusCmd_NodePdoRead(self.handle, ctypes.c_int(inode), ctypes.c_int(index),
                                          ctypes.c_int(subindex), ctypes.c_int(type), ctypes.byref(value))
    return ret, value