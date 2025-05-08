import time
import logging
from commanduino import CommandManager
import numpy as np
from scipy import stats

class pHTestMeter:
    """
    Consist of an arduino board and a pH data collector.
    """

    def __init__(self, port: str, logger: logging.Logger):
        """
        Initialize the config of arduino.

        Args:
            port: the port of the arduino board.
        """
        self.port = port
        self.logger = logger
        self.config = {
            "ios" : [
                {
                "port": self.port
                },
            ],
            "devices": {
                "A1": {
                "command_id": "A1"
                }
            }
        }
        
        self.arduino = CommandManager.from_config(self.config)
        self.reference_pH = {}
        self.calibrated = False 

    def get_temp_pH(self) -> float:
        """
        Read temp_pH.

        Returns:
            the temp pH 
        """
        # read the analog 10 times.
        buf = []
        for i in range(10):
            buf.append(self.arduino.A1.get_level())
            time.sleep(0.03)
        # throw away the 2 biggest and 2 smallest value, then calculate the average of leftover
        buf.sort()
        avgValue = np.mean(buf)
        
        return avgValue
    
    def reset_ref(self):
        """
        Emtpy the list of the refernece sampling
        """

        self.reference_pH = {}

    def record_ref(self, ref_pH: float) -> tuple:
        """
        Calibrate the linear fit to get the accurate pH, the first point.

        Args:
            ref_pH_0: the known pH of the reference solution.
        """
        self.reference_pH[ref_pH] = self.get_temp_pH()
        self.logger.info(f"reference record succeed. current reference is {self.reference_pH}.")

   
    def calibrate_meter(self):
        """
        Calculate the slope and offset of the pH linear curve.
        !!! ATTENTION: this function must be used after func: record_ref
        """
        # calculate the slope and offset of the pH linear curve
        x = list(self.reference_pH.values())
        y = list(self.reference_pH.keys())
        self.res = stats.linregress(x, y)

        self.logger.info(f"meter_correction succeed. the R2 is {self.res.rvalue**2:.6f}")
        self.calibrated = True 
    def read_pH(self) -> float:
        """
        Read current_pH (maybe not correct).

        Returns:
            the current_pH (maybe not correct)
        """
        if self.calibrated:
            # calculate the current by using the linear curve
            current_pH = self.res.slope * self.get_temp_pH() + self.res.intercept
            current_pH = round(float(current_pH), 2)
        else:
            raise ValueError("The pH meter is not calibrated before measuring the pH value.")
        return current_pH
        