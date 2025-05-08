import MS_hotplate
import logging
import time
DEFAULT_STIR_SPEED = 500

class HotPlate_op:
    """
    Include the operations of DL hotplate.
    Operations:
        none
    """
    def __init__(self, 
                 hotplate: MS_hotplate.HotPlateController, 
                 logger: logging.Logger) -> None:
        """
        initialzie the device
        """
        # initialize the hotplate
        self.hotplate = hotplate
        self.logger = logger
        self.hotplate.hello_device()

    def stir(self, stir_time: float, sitr_speed: int = DEFAULT_STIR_SPEED):
        """
        Stir for duration time.

        Args:
            sitr_speed: the speed of magentic sitr, unit: rpm.
            stir_time: the time of stir.
        """
        self.hotplate.set_rpm(sitr_speed)
        self.hotplate.turn_stir_on()
        time.sleep(stir_time)
        self.hotplate.turn_heater_off()