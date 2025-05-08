import logging
from zmotion import AxisMotion
from runze_driver import SyringePump
from typing import Optional, List

class Valve:
    """
    A class used to control valve by IO and relay.
    """
    def __init__(self, axismotion: AxisMotion, op_index: str) -> None:
        """
        Set the output port of the relay

        Args:
            axismotion: the controller IO module object
            op_index: the index of relay
        """
        self.axismotion = axismotion
        self.op_index = op_index

    def switch_on(self):
        """
        Set the high signal of output port.
        """
        self.axismotion.output_trigger(self.op_index, True)
    
    def switch_off(self):
        """
        Set the low signal of output port.
        """
        self.axismotion.output_trigger(self.op_index, False)

class SyringePump_with_Valve:
    """
    A class combine with the SY-08 syringe pump and magnetic valve.
    """
    def __init__(self, pump: SyringePump, valve: Valve, logger: logging.Logger) -> None:
        """
        initialize the devices, pump and valve.

        Args:
            pump: the SyringePump object from runze driver
            valve: the valve object
            logger: the logger
        """
        self.pump = pump
        self.valve = valve
        self.logger = logger
        
    def dispense_liquid(self, volume: float):
        """
        Dispense liquid.

        Args:
            volume: the volume of added liquid
        """
        self.pump.set_dynamic_speed(0.5)
        # low the speed when the added volume is lower than 0.15 mL.
        if volume < 0.15:
            self.pump.set_dynamic_speed(0.05)

        while volume > self.pump.volume:
            self.valve.switch_off()
            self.pump.move_to_absolute_position(self.pump.volume)
            self.valve.switch_on()
            self.pump.move_to_absolute_position(0)
            self.valve.switch_off()
            volume -= self.pump.volume
        self.valve.switch_off()
        self.pump.move_to_absolute_position(volume)
        self.valve.switch_on()
        self.pump.move_to_absolute_position(0)
        self.valve.switch_off()
