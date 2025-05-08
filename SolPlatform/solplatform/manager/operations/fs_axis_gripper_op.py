import time
import threading
import logging
from Gas_controller import GASAxis
from dh_gripper import Gripper
from runze_driver import SwitchValve

DEFAULT_PUMP_SPEED = 200

class FS_Axis_Gripper_op:
    """
    the operation of multi-axis, dh-rgi100 gripper, runze SV-07 valve
    """
    def __init__(self, 
                 gasaxis: GASAxis, 
                 rgi100: Gripper, 
                 valve: SwitchValve, 
                 coordinates: dict, 
                 valve_channels: dict, 
                 solvent_factor: dict, 
                 logger: logging.Logger) -> None:
        # initialization
        # initialize the devices
        self.gasaxis = gasaxis
        self.rgi100 = rgi100
        self.valve = valve
        # initialize the config
        self.coordinates = coordinates
        self.valve_channels = valve_channels
        self.solvent_factors = solvent_factor
        self.tube_volume = 2.08
        # initialize the logger
        self.logger = logger
        # axis connection and return home
        self.gasaxis.connection()
        self.gasaxis.datum_xyz()
        # gripper initialization
        self.rgi100.initialization()
        self.rgi100.set_force(50)
        self.gripper_sts = 1
        # switch valve initialization
        self.valve.restoration()
        # IO devices initialization
        self.gasaxis.output_trigger('air_gripper', False)
        self.gasaxis.output_trigger('stir', False)
        self.gasaxis.output_trigger('actuator', False)
        self.gasaxis.output_trigger('actuator', True)
        self.gasaxis.output_trigger('magnetic', False)
        self.actuator_sts = True
        self.air_gripper_sts = False
        self.stir_sts = False
        self.magnetic_sts = False

    def actuator(self, onoff: bool) -> bool:
        """
        Use controller IO module to control relay to control actuator.

        Args:
            onoff: the status of actuator.
        """
        if onoff:
            if self.actuator_sts:
                return True
            else:
                self.gasaxis.output_trigger('actuator', True)
                time.sleep(6)
                self.actuator_sts = True
        else: 
            if self.actuator_sts: 
                self.gasaxis.output_trigger('actuator', False)
                time.sleep(6)
                self.actuator_sts = False
            else:
                return True
            
    def air_gripper(self, onoff: bool) -> bool:
        """ 
        Use controller IO module to control relay to AirTAC air_gripper.

        Args:
            onoff: the status of air_gripper.
        """
        if onoff:
            if self.air_gripper_sts:
                return True
            else:
                self.gasaxis.output_trigger('air_gripper', True)
                time.sleep(1)
                self.air_gripper_sts = True
        else: 
            if self.air_gripper_sts: 
                self.gasaxis.output_trigger('air_gripper', False)
                time.sleep(1)
                self.air_gripper_sts = False
            else:
                return True
            
    def stir(self, onoff: bool) -> bool:
        """ 
        Use controller IO module to control relay to magnetic stir.

        Args:
            onoff: the status of stirer.
        """
        if onoff:
            if self.stir_sts:
                return True
            else:
                self.gasaxis.output_trigger('stir', True)
                self.stir_sts = True
        else: 
            if self.stir_sts: 
                self.gasaxis.output_trigger('stir', False)
                self.stir_sts = False
            else:
                return True
            
    def magnetic(self, onoff: bool) -> bool:
        """ 
        Use controller IO module to control relay to elec magnetic iron.

        Args:
            onoff: the status of magnetic iron.
        """
        if onoff:
            if self.magnetic_sts:
                return True
            else:
                self.gasaxis.output_trigger('magnetic', True)
                self.magnetic_sts = True
        else: 
            if self.magnetic_sts: 
                self.gasaxis.output_trigger('magnetic', False)
                self.magnetic_sts = False
            else:
                return True

    def swtich_gripper(self, gripper_sts: str) -> bool:
        """
        Switch the status of gripper by datum axis and rotating 180 degree.

        Args:
            gripper_sts: the sts of gripper, e.g. 'front', 'down' 
        """
        self.rgi100.set_rotation_speed(40)
        if gripper_sts == 'down':
            if self.gripper_sts != 0: 
                self.gasaxis.move_xyz([0, 0, 0])
                self.rgi100.set_rotation_angle((self.gripper_sts) * 180)
                self.gripper_sts = 0
            return True
        elif gripper_sts == 'front':
            if self.gripper_sts == 0:
                self.gasaxis.move_xyz([0, 0, 0])
                self.rgi100.set_rotation_angle((self.gripper_sts - 1) * 180)
                self.gripper_sts = 1
            return True
        else: 
            raise ValueError(f"gripper_sts must be 'down', or 'front', currnet value is {gripper_sts}.")
            
        
    def get_obj(self, target: str, idx: int) -> bool:
        """
        Get object.

        Args:
            plate: the place where the object is in.
            idx: the object index.
        """
        self.swtich_gripper("down")
        self.rgi100.set_site(1000)
        self.gasaxis.move_xyz(self.coordinates[target][idx])
        self.rgi100.set_site(0)
        return True

    def place_obj(self, target: str, idx: int, open: bool = True) -> bool:
        """
        Place object.

        Args:
            plate: the place where the object is in.
            idx: the object index.
        """
        self.swtich_gripper("down")
        self.gasaxis.move_xyz(self.coordinates[target][idx])
        if open:
            self.rgi100.set_site(1000)
            return True
        else:
            return True

    def prepare_bottle(self, stir_time: int = 10):
        """
        Prepare the reactor: get the bottle and stir the mixture.
        Args:
            stir_time: the time of stir
        """
        # to get the bottle bottom
        self.swtich_gripper('front')
        self.air_gripper(False)
        self.actuator(False)
        self.air_gripper(True)
        self.actuator(True)
        # the rgi100 catch the half of the bottle
        self.gasaxis.move_xyz(self.coordinates['prepare_bottle_route'][0])
        self.gasaxis.trap('x', self.coordinates['prepare_bottle_route'][1])
        self.rgi100.set_site(0)
        self.air_gripper(False)
        self.gasaxis.trap('x', self.coordinates['prepare_bottle_route'][2])
        # move the bottle to the magnetic stir, stir it for some time
        self.gasaxis.move_xyz(self.coordinates['stir'][0])
        self.stir(True)
        time.sleep(stir_time)
        self.stir(False)

    def return_bottle(self):
        """
        Return the bottle back to its holder after dumping mixture.
        ATTENTION: This function must be used after 'dump_mixture' func!!!
        """
        self.gasaxis.move_xyz(self.coordinates['prepare_bottle_route'][0])
        self.gasaxis.trap('x', self.coordinates['prepare_bottle_route'][1])
        self.air_gripper(True)
        self.rgi100.set_site(1000)
        self.gasaxis.trap('x', self.coordinates['prepare_bottle_route'][2])
        self.actuator(False)
        self.air_gripper(False)
        self.actuator(True)

    def pump(self, channel: str, speed: int = 200, open_time: float = 15):
        """
        Open the pump by some speed.

        Args:
            speed: the speed of pump, unit: rpm.
        """
        self.valve.valve_switch(self.valve_channels, channel)
        self.gasaxis.jog('pump', speed)
        self.logger.info(f'pump is open, current speed is {speed} rpm.')
        time.sleep(open_time)
        self.gasaxis.jog('pump', 0)
        self.logger.info(f'pump is stop, open time is {open_time} s.')
        return True

    def dump_mixture(self, target_idx: int):
        """
        Dump the stirred the mixture.

        Args:
            target_idx: the unused funnel index.
        ATTENTION: This function must be used after 'prepare_funnel' func!!!
        """
        # judge the whether the index is in the capacity
        if target_idx in range(0, 4, 1):
            dir = 1
        elif target_idx in range(4, 8, 1): 
            dir = -1
        else:
            raise ValueError(f'target_idx should be int and smaller than 8, current value is {target_idx}')
        # dump mixture into funnel
        self.gasaxis.move_xyz(self.coordinates['dumped_bottle'][target_idx])
        self.rgi100.set_rotation_speed(5)
        self.magnetic(True)
        time.sleep(1)
        y = threading.Thread(target = self.gasaxis.trap, args=('y', self.coordinates['dumped_bottle'][target_idx][1] - 8 * dir))
        r = threading.Thread(target = self.rgi100.set_rotation_angle, args=(-120 * dir, 1))
        r.start()
        time.sleep(1.3)
        y.start()
        y.join()
        r.join()
        time.sleep(20)
        # reset the gripper
        self.rgi100.set_rotation_angle(120 * dir)
        self.rgi100.set_rotation_speed(40)
        self.magnetic(False)
    
    def lean_funnel(self, target_idx, waiting_time): 
        """
        Lean the funnel to accelerate the filtration.

        Args:
            target_idx: funnel_index
            waiting_time: the filtration time
        """
        # judge the whether the index is in the capacity
        if target_idx in range(0, 4, 1):
            dir = 1
        elif target_idx in range(4, 8, 1): 
            dir = -1
        else:
            raise ValueError(f'target_idx should be int and smaller than 8, current value is {target_idx}')
        self.get_obj("liquid_accpters", target_idx)
        self.gasaxis.trap("z", self.coordinates["liquid_accpters"][target_idx][2] - 20)
        self.rgi100.set_rotation_speed(1)
        self.rgi100.set_rotation_angle(20 * dir)
        self.gasaxis.trap("y", self.coordinates["liquid_accpters"][target_idx][1] + dir * 30)
        time.sleep(waiting_time)
        gripper = threading.Thread(target = self.rgi100.set_rotation_angle, args=(-20 * dir, ))
        move = threading.Thread(target = self.gasaxis.trap, args = ("y", self.coordinates["liquid_accpters"][target_idx][1]))
        move.start()
        time.sleep(0.1)
        gripper.start()
        gripper.join()
        move.join()
        self.rgi100.set_rotation_speed()
        self.place_obj("liquid_accpters", target_idx)

    def prepare_funnel(self, funnel_idx: int):
        """
        Put funnel on the top of liquid accpter.

        Args:
            funnel_idx: unused funnel
        """
        self.swtich_gripper('down')
        self.get_obj('funnel_holders', funnel_idx)
        self.place_obj('liquid_accpters', funnel_idx)

    def return_funnel(self, funnel_idx: int):
        """
        Put funnel back to its holder.

        Args:
            funnel_idx: used funnel

        ATTENTION: This function must be used after 'return_bottle' func!!!
        """
        self.swtich_gripper('down')
        self.get_obj('liquid_accpters', funnel_idx)
        self.place_obj('funnel_holders', funnel_idx)

    def clean_tube(self, 
                   wash_speed: int = DEFAULT_PUMP_SPEED, 
                   wash_time: float = 5):
        """
        Push the solution out of the tube into waste.

        Args:
            wash_speed: the speed of the pump, unit: rpm.
            wash_time: the time of washing.
        """
        self.pump("wasteout", -1 * wash_speed, wash_time)

    def preflush(self, solvent: str):
        self.clean_tube()
        self.pump(solvent, 
                  speed = 200, 
                  open_time = self.tube_volume / self.solvent_factors[solvent])


    def wash_mixture(self, 
                     target_idx: int, 
                     solvent: str = 'H2O', 
                     wash_repeat: int = 1, 
                     speed: int = DEFAULT_PUMP_SPEED, 
                     wash_time: float = 20, 
                     waiting_time: float = 60*30): 
        """
        Use chosen solvent to wash the mixture in the funnel.

        Args:
            target_idx: the index of mixture
            solvent: the used solvent. Defaults to 'H2O'.
            speed: the pump speed. Defaults to 100.
            wash_time: the time of washing. Defaults to 10.
        """
        # switch the gripper
        self.swtich_gripper("down")
        self.preflush(solvent)
        # switch the valve to the chosen solvent
        self.valve.valve_switch(self.valve_channels, solvent)
        # put the feeder on the top of mixture and open the pump to wash it
        self.get_obj('feeder', 0)
        self.place_obj('wash', target_idx, False)
        # begin to wash 
        for i in range(wash_repeat):
            self.pump(solvent, speed, wash_time)
            time.sleep(wash_time*0.2) #FIXME 
        # after washing, push the liquid that is in the tube into waste
        self.clean_tube()
        # place the feeder to where it should be
        self.place_obj('feeder', 0, True)
        self.get_obj("liquid_accpters", target_idx)
        self.gasaxis.trap("z", self.coordinates["liquid_accpters"][target_idx][2] - 10)
        time.sleep(waiting_time)
        self.place_obj("liquid_accpters", target_idx, False)
        self.place_obj("funnel_holders", target_idx)