import logging
from runze_driver import SyringePump, SwitchValve

URTRA_SLOW_SPEED = 0.1
SLOW_SPEED = 0.7
MID_SPEED = 1
HIGH_SPEED = 1.75

class SyringePump_op:
    """
    Include the operations of Runze syringepump SY-03B and Runze switchvalve SV-07.

    Operations:
        Absorb liquid from a given channel.
        Inject liquid to a given channel.
        Dispense liquid froma a channel to another channel.
        Preflush, Airflush...
    """
    def __init__(self, 
                 syringe_pump: SyringePump, 
                 switch_valve: SwitchValve, 
                 syringe_pump_channels: dict, 
                 switch_valve_channels: dict, 
                 logger: logging.Logger) -> None:
        """
        initialze the operation of the syringe pumps

        Args:
            syringe_pump: a SyringePump object that is responsible for the communication with the syringe_pump 
            switch_valve: a SwitchValve object that is responsible for the communication with the switch_valve 
            syringe_pump_channels: a dict that is contains names of channels on syringe_pump
            switch_valve_channels: a dict that is contains names of channels on switch_valve
            logger: logger
        """
        # initialize the devices
        self.syringe_pump = syringe_pump
        self.switch_valve = switch_valve
        # initialize the channels
        self.syringe_pump_channels = syringe_pump_channels
        self.switch_valve_channels = switch_valve_channels
        self.syringe_pump.valve_restoration()
        self.switch_valve.restoration()
        self._switch_valve("syringe_pump", "wasteout")
        self.syringe_pump.forced_reset()
        # initialize the logger
        self.logger = logger
        self.dispense_liquid(5, "air", "wasteout")

    def _switch_valve(self, device_name: str, channel: str):
        """
        judge the device is wheather switch_valve or syringe_pump, than switch to the channel

        Args:
            device_name: the name of device contains valve, e.g. 'switch_valve', 'syringe_pump'
            channel: the name of the channel that is on the chosen device
        """
        # if device is switch_valve
        if device_name == "switch_valve": 
            self.switch_valve.valve_switch(param = self.switch_valve_channels, 
                                           channel = channel)
        # if the device is syringe_pump
        elif device_name == "syringe_pump":
            self.syringe_pump.valve_switch(param = self.syringe_pump_channels, 
                                           channel = channel)
        else:
            raise ValueError(f"device name should be switch_valve of syringe_pump, current value is {device_name}")

    def absorb_liquid(self, volume: float, inlet_channel, in_speed = SLOW_SPEED):
        """
        absorb liquid from a given channel

        Args:
            volume: the volume of liquid absorbed
            inlet_channel: the channel that link the liquid
            in_speed: absorb speed
        """
        # judge the target channel is on syringepump or switchvalve, and switch to it
        if inlet_channel in list(self.syringe_pump_channels.keys()):
            self._switch_valve("syringe_pump", inlet_channel)
        elif inlet_channel in list(self.switch_valve_channels.keys()):
            self._switch_valve("syringe_pump", "switch_valve")
            self._switch_valve("switch_valve", inlet_channel)
        else:
            raise ValueError(f"{inlet_channel} is not a supported channel in the current set-up!")
        # if volume is larger than the amount wanted, raise error; else absorb liquid
        if volume > self.syringe_pump.volume:
            raise ValueError(f"The volume should less than {self.syringe_pump.volume}, current value is {volume}.")
        else:
            self.syringe_pump.set_dynamic_speed(in_speed)
            self.syringe_pump.move_to_absolute_position(volume)
           
    
    def inject_liquid(self, outlet_channel: str, out_speed = HIGH_SPEED):
        """
        inject liquid to a given channel

        Args:
            volume: the volume of liquid absorbed
            outlet_channel: the channel where 
            out_speed: inject speed
        """
        # judge the target channel is on syringepump or switchvalve, and switch to it
        if outlet_channel in list(self.syringe_pump_channels.keys()):
            self._switch_valve("syringe_pump", outlet_channel)
        elif outlet_channel in list(self.switch_valve_channels.keys()):
            self._switch_valve("syringe_pump", "switch_valve")
            self._switch_valve("switch_valve", outlet_channel)
        else:
            raise ValueError(f"{outlet_channel} is not a supported channel in the current set-up!")
        # inject the liquid
        self.syringe_pump.set_dynamic_speed(out_speed)
        self.syringe_pump.move_to_absolute_position(0)

    def dispense_liquid(self, volume: float, inlet_channel: str, outlet_channel: str, in_speed = SLOW_SPEED, out_speed = HIGH_SPEED):
        """
        dispense liquid from an inlet channel to an outlet channel

        Args:
            volume: the volume of liquid dispense
            inlet_channel: the channel that link to the input of liquid
            outlet_channel: the channel that link to the output of liquid
            in_speed: the absorb speed
            out_speed: the inject speed
        """
        while volume > 0:
            # dispense liquid multiple times if volume is larger than the max volume of syringe_pump
            if volume > self.syringe_pump.volume:
                self.absorb_liquid(self.syringe_pump.volume, inlet_channel, in_speed)
                self.inject_liquid(outlet_channel, out_speed)
                volume = volume - self.syringe_pump.volume
            # dispense liquid once
            else:
                self.absorb_liquid(volume, inlet_channel, in_speed)
                self.inject_liquid(outlet_channel, out_speed)
                volume = 0
        
    def preflush(self, volume: float, inlet_channel: str, outlet_channel: str, in_speed, out_speed = HIGH_SPEED):
        """
        preflush when needed

        Args:
            volume: the volume of liquid dispense
            inlet_channel: the channel that link to the input cell of liquid
            outlet_channel: the channel that link to the output cell of liquid
            in_speed: the absorb speed
            out_speed: the inject speed
        """
        # dispense liquid
        self.dispense_liquid(volume, inlet_channel, outlet_channel, in_speed, out_speed)
        
    def air_flush(self, solvent: str, cell_channel: str, out_speed: float = HIGH_SPEED):
        """
        flush by air and solvent

        Args:
            solvent: the name of solvent use to flush
            cell_channel: target cell wanted to be flushed
        """
        # wash the syringe_pump by chosen solvent twice
        for i in range(2):
            self.dispense_liquid(volume = self.syringe_pump.volume,
                                inlet_channel = solvent,
                                outlet_channel = "wasteout",
                                in_speed = MID_SPEED,
                                out_speed = out_speed)
        # wash the syringe_pump by air twice
        for i in range(2):
            self.dispense_liquid(volume = 2,
                                inlet_channel = "air",
                                outlet_channel = "wasteout",
                                in_speed = MID_SPEED,
                                out_speed = out_speed)
        # inject air into the target cell twice
        for i in range(2):
            self.dispense_liquid(volume = 2,
                                 inlet_channel = "air",
                                 outlet_channel = cell_channel,
                                 in_speed = MID_SPEED,
                                 out_speed = URTRA_SLOW_SPEED)
    
    def pipette_liquids(self, volume: float, channel: str, cell_channel: str, out_speed: float = HIGH_SPEED) -> None:
        """
        dispense liquid into a cell
        Args:
            volume: volume of the liquid in mL
            channel: inlet channel
            cell_channel: the outlet channel
            preflush: if we should preflush the syringe and the tube
        return: 
            none
        """
        # preflush
        if channel in self.switch_valve_channels:
            self.preflush(volume = 4.0,
                          inlet_channel = channel,
                          outlet_channel = "wasteout",
                          in_speed = MID_SPEED,
                          out_speed = HIGH_SPEED)
        else:
            self.preflush(volume = 2.0,
                          inlet_channel = channel,
                          outlet_channel = "wasteout",
                          in_speed = MID_SPEED,
                          out_speed = HIGH_SPEED)
        # add liquid
        self.dispense_liquid(volume,
                             inlet_channel = channel,
                             outlet_channel = cell_channel,
                             in_speed = SLOW_SPEED,
                             out_speed = out_speed)
        # flush by air
        self.air_flush("H2O", cell_channel)