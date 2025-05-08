from llmlab.operations.exp_operation.basic_step import BasicStep
from llmlab.utlis.property import Property
from typing import Union
from .attribute_value import *

from copy import copy 
from llmlab.utlis.interactions import ask_for_physical_property, standardize_unit

class StirForDuration(BasicStep):
    """
    Stir the reactor with certain speed for certain amount of time
    Args:
        reactor_name: str, mandatory
            The name of the reactor.
        
        duration: Union[Dict[str, Any], str], mandatory
            Represents the duration of the stirring, which can be in one of the following formats:
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 2.0, "unit": "days"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 1.0, "unit": "hours"}, "max": {"quantity": 3.0, "unit": "hours"}}
            3. **Descriptive string**: A string describing the duration qualitatively.
        
        temperature: Union[Dict[str, Any], str, None], optional
            Represents the temperature of the stirring process, which can be in one of the following formats. If not clearly defined but referred to as room temperature, use "{"quantity": 20.0, "unit": "℃"}".
            1. **Single value**: A dictionary following the "Property" format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 20.0, "unit": "℃"}
            2. **Range**: A dictionary with min and max values, each following the "Property" format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 18.0, "unit": "℃"}, "max": {"quantity": 22.0, "unit": "℃"}}
            3. **Descriptive string**: A string describing the temperature qualitatively (e.g., "room temperature", "warm").
        
        stir_speed: Union[Dict[str, Any], str, None], optional
            Represents the stirring intensity or precise stirring speed. Defaults to "{"quantity": 300, "unit": "rpm"}" if the exact speed is not mentioned.
            1. **Single value**: A dictionary following the "Property" format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 500, "unit": "rpm"}
            2. **Range**: A dictionary with min and max values, each following the "Property" format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 400, "unit": "rpm"}, "max": {"quantity": 800, "unit": "rpm"}}
            3. **Descriptive string**: A string describing the stirring intensity qualitatively (e.g., "vigorously", "gently", "softly").
    """
    def __init__(self,
                 reactor_name: str,
                 duration: dict,
                 temperature: dict = None,
                 stir_speed: Union[dict[float, str], str, None] = None
                 ):
        
        super().__init__()   
                  
        self.reactor_name = str(reactor_name)

        # if the temperature is None, we set it to 20 degrees
        if temperature is None:
            self.temperature = None
        else:
            self.temperature = parse_temperature(temperature)
    
        # define the stirring speed (if it is None, default to 300 rpm)
        if stir_speed is None:
            self.stir_speed = Property(quantity=300, unit = "rpm")
        else:
            self.stir_speed = parse_property(stir_speed)
        
        # define the duration 
        self.duration = parse_property(duration)
    
    def check_ambiguity(self, mode = "plain_txt"):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        # find the potentially ambiguious quantity 
        self.ambiguity_dict = {}
        
        # the stir_speed must be property 
        if not isinstance(self.stir_speed, Property):
            self.ambiguity_dict["stir_speed"] = copy(self.stir_speed)
            
        # the duration must be property 
        if not isinstance(self.duration, Property):
            self.ambiguity_dict["duration"] = copy(self.duration)
            
        # the temperature can either be property or None 
        if not (isinstance(self.temperature, Property) or self.temperature == None):
            self.ambiguity_dict["temperature"] = copy(self.temperature)
            
        # update the attribute after giving the new value 
        for key, value in self.ambiguity_dict.items():
            new_property = ask_for_physical_property(key, value, mode = mode)
            if isinstance(new_property, Property):
                standardize_unit(None, key, new_property, property_type = key)
            setattr(self, key, new_property)
        
class StartStir(BasicStep):
    """
    Trigger to stir the reactor at a certain speed.
    Args:
        reactor_name: str, mandatory
            The name of the reactor.
        stir_speed: Union[Dict[str, Any], str, None], optional
            Represents the stirring intensity or the precise stirring speed. Default to "{"quantity": 300, "unit": "rpm"}" if the stirring speed is not mentioned. 
            1. **Single value**: A dictionary following the "Property" format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 500, "unit": "rpm"}
            2. **Range**: A dictionary with min and max values, each following the "Property" format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 400, "unit": "rpm"}, "max": {"quantity": 800, "unit": "rpm"}}
            3. **Descriptive string**: A string describing the stirring intensity qualitatively (e.g., "vigorously", "gently", "softly").
    """
    
    def __init__(self, 
                 reactor_name: str,
                 stir_speed: Union[dict[float, str], str, None] = None):
        
        super().__init__()
        
        self.reactor_name = str(reactor_name)
        
        # define the stirring speed
        if stir_speed is None:
            self.stir_speed = Property(quantity=300, unit = "rpm")
        else:
            self.stir_speed = parse_property(stir_speed)
    
    def check_ambiguity(self, mode = "plain_txt"):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        # find the potentially ambiguious quantity 
        self.ambiguity_dict = {}        
        if not isinstance(self.stir_speed, Property):
            self.ambiguity_dict["stir_speed"] = copy(self.stir_speed)
            
        # update the attribute after giving the new value 
        for key, value in self.ambiguity_dict.items():
            new_property = ask_for_physical_property(key, value, mode = mode)
            if isinstance(new_property, Property):
                standardize_unit(None, key, new_property, property_type = key)
            setattr(self, key, new_property)
            
class StopStir(BasicStep):
    """
    Trigger to stop the stirring of the reactor.
    Args:
        reactor_name: str type. the name of the reactor
    """
    def __init__(self, 
                 reactor_name: str):
        
        super().__init__()
        
        self.reactor_name = str(reactor_name)
    
    def check_ambiguity(self, mode = "plain_txt"):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        pass 