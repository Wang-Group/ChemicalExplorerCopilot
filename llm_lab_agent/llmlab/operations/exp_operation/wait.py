from llmlab.operations.exp_operation.basic_step import BasicStep
from llmlab.utlis.property import Property
from .attribute_value import *

from copy import copy 
from llmlab.utlis.interactions import ask_for_physical_property, standardize_unit

class Wait(BasicStep):
    """
    Wait for some time
    
    Args:
        time: Union[Dict[str, Any], str], mandatory
            Represents the duration of the wait process, which can be in one of the following formats:
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 2.0, "unit": "days"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 1.0, "unit": "hours"}, "max": {"quantity": 3.0, "unit": "hours"}}
            3. **Descriptive string**: A string describing the duration qualitatively.
    """
    def __init__(self, 
                 time: dict):
        
        super().__init__()
        if time is None:
            raise ValueError(f"the time can not be None.")
        else:
            self.time = parse_property(time)
    
    def check_ambiguity(self, mode = "plain_txt"):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        pass 