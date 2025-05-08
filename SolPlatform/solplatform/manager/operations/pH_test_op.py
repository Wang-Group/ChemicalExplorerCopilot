import logging
import time
from numpy import average
from ..utility import *
from ..drivers.custom_pump import SyringePump_with_Valve
from pHTestuino import pHTestMeter
from runze_driver import PeristalticPump
from typing import Optional, List
import numpy as np 
from Gas_controller import GASAxis

class pH_Test_op:

    def __init__(self, 
                 pHmeter: pHTestMeter, 
                 pump_waste: PeristalticPump, 
                 pump_water: PeristalticPump, 
                 pump_KCl: PeristalticPump, 
                 pump_acid:  Optional[SyringePump_with_Valve] = None, 
                 pump_base: Optional[SyringePump_with_Valve] = None, 
                 LS_pH_multi_axis: GASAxis = None,
                 logger: Optional[logging.Logger] = None) -> None:
        
        # initialize the devices
        self.pHmeter = pHmeter

        # define the pumps to be used 
        self.pump_water = pump_water
        self.pump_waste = pump_waste
        self.pump_KCl = pump_KCl

        # use the acid and base pump (stay with the pH meter)
        self.pump_acid = pump_acid
        self.pump_base = pump_base

        # initialize the pumps
        self.pump_acid.pump.forced_reset()
        self.pump_base.pump.forced_reset()

        # initialize the axis 
        self.LS_pH_multi_axis = LS_pH_multi_axis
        self.LS_pH_multi_axis.connection()
        # initialize the logger
        self.logger = logger
        
        # get the locations of the spins
        self.spin_locations = [-0.8, 36.2, 44.7, 53.7, 89.8] # storage location. buffer1. buffer 2. buffer 3. solution loc. 
        self.z_location = 95 # the distance that the z axis should move
        self.storage_z_location = 100
        self.current_spin = None
        self.current_z = None

        # initialize the pH meter
        self.home_pH_meter()
        # move the pH meter to the bottle
        self.move_pH_meter_to(self.spin_locations[0], self.storage_z_location)
        self.LS_pH_multi_axis.jog("stir_storage", 600)
        
    def initialize_pH_sys(self):
        
        # move the pH meter to the bottle
        self.move_pH_meter_to(self.spin_locations[0], self.storage_z_location)
        self.pump_acid.dispense_liquid(2)
        self.pump_base.dispense_liquid(2)
        
        self.clean_cell(cycle_num = 1)


    def home_pH_meter(self):
        """
        Move the pH meter to its home position 
        """
        self.LS_pH_multi_axis.return_home("z")
        self.LS_pH_multi_axis.return_home("spin")
        # update the location 
        self.current_spin = 0 
        self.current_z = 0
        
    def move_pH_meter_to(self, spin: float, z: float):
        """
        Move the pH meter to a specific location
        """
        if self.current_spin != spin:
            self.LS_pH_multi_axis.trap("z", 0, 20)
            self.LS_pH_multi_axis.trap("spin", spin, 20)
        self.LS_pH_multi_axis.trap("z", z, 20)
        # update the location 
        self.current_spin = spin 
        self.current_z = z 
        
    def clean_cell(self, cycle_num: int = 3):
        """
        Clean the cell that holds pH and KCl
        Args:
            cycle_num: the cleaning cycle number
        """
        # clean the pH storage cell
        self.pump_waste.pump_liquid(300, 20)
        # the volume of water should be higher than KCl, as well as the depth of the pH meter in the solution
        for i in range(cycle_num):
            self.pump_water.pump_liquid(-300, 17)
            self.pump_waste.pump_liquid(300, 20)

    def refresh_KCl(self):
        """
        Add a fresh KCl solution to the cell
        """
        # empty the pH storage cell just in case 
        self.pump_waste.pump_liquid(300, 20)
        # add the KCl solution
        self.pump_KCl.pump_liquid(-300, 15)
        
    def read_pH(self):
        """
        Read the pH value of the current environment
        """
        buf = []
        for i in range(10):
            buf.append(self.pHmeter.read_pH())
            time.sleep(0.03)

        # throw away the 2 biggest and 2 smallest value, then calculate the average of leftover
        while max(buf) - min(buf) > 0.1:
            buf = []
            for i in range(10):
                buf.append(self.pHmeter.read_pH())
                time.sleep(0.03)
                
        return np.mean(buf)
    
    def _magnetic_stir(self, stir_time: float, stir_speed: int = 300): 
        """
        magnetic stir in uv_vis_holder

        Args:
            stir_time: the time of stir
            stir_speed: the speed of stir, unit: rpm
        """
        self.LS_pH_multi_axis.jog("stir", stir_speed)
        time.sleep(stir_time)
        self.LS_pH_multi_axis.jog("stir", 0)