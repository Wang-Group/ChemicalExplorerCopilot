from llmlab.operations.exp_operation.basic_step import BasicStep
from llmlab.utlis.property import Property
from typing import Union
from .attribute_value import *

from copy import copy 
from llmlab.utlis.interactions import ask_for_physical_property, standardize_unit

class Evaporate(BasicStep):
    """
    Evaporate solvent from a solution inside a reactor.

    Args:
        reactor_name: str, mandatory
            The name of the reactor from the "Reactor" class, where the solvent will be evaporated from.
        
        pressure: Union[Dict[str, Any], str, None], optional
            Represents the vacuum pressure for the evaporation, which can be in one of the following formats. Defaults to null, which means no vacuum was used.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 0.8, "unit": "Pa"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 0.5, "unit": "atm"}, "max": {"quantity": 1.0, "unit": "atm"}}
            3. **Descriptive string**: A string describing the pressure qualitatively (e.g., "low", "medium", "high").
        
        stir: bool, optional
            Indicates if stirring should be applied during the process. Defaults to false.
        
        stir_speed: Union[Dict[str, Any], str, None], optional
            Represents the stirring intensity during the evaporation, which can be in one of the following formats. It should be null if stir is not applied or the exact speed is not mentioned. Defaults to null.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 500, "unit": "rpm"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 400, "unit": "rpm"}, "max": {"quantity": 800, "unit": "rpm"}}
            3. **Descriptive string**: A string describing the stirring intensity qualitatively (e.g., "vigorously", "gently", "softly").
        
        temperature: Union[Dict[str, Any], str, None], optional
            Represents the target temperature, temperature range, or a descriptive string (e.g., "hot", "cool"), which can be in one of the following formats. If it is a specific value, follow the format from the "Property" class. Defaults to "20 ℃".
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 20.0, "unit": "℃"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 18.0, "unit": "℃"}, "max": {"quantity": 22.0, "unit": "℃"}}
            3. **Descriptive string**: A string describing the temperature qualitatively (e.g., "warm", "hot").
        
        duration: Union[Dict[str, Any], str, None], optional
            Represents the time for evaporation, which can be in one of the following formats. Defaults to null.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 2.0, "unit": "hours"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 1.0, "unit": "hours"}, "max": {"quantity": 3.0, "unit": "hours"}}
            3. **Descriptive string**: A string describing the duration qualitatively.
    """
    
    def __init__(self, 
                 reactor_name: str, 
                 pressure: str = None, 
                 stir: bool = False, 
                 stir_speed: Union[dict[float, str], str] = None,
                 temperature: dict = None,
                 duration: dict = None):
        super().__init__()
        
        self.reactor_name = str(reactor_name)
        self.pressure = parse_property(pressure)
        
        # define the stirring speed
        self.stir = bool(stir)
        self.stir_speed = parse_property(stir_speed)
        if self.stir == False and self.stir_speed != None:
            raise ValueError(f"The stir is off and the stiring speed ({self.stir_speed}) is defined!")
            
        if temperature is None:
            self.temperature = Property(quantity = 20, unit="℃")
        else:
            self.temperature = parse_temperature(temperature)
            
        self.duration = parse_property(duration)
        
    def check_ambiguity(self, mode = "plain_txt"):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        # find the potentially ambiguious quantity 
        self.ambiguity_dict = {}      
          
        # the pressure should be a property or None 
        if not (isinstance(self.pressure, Property) or self.pressure == None):
            self.ambiguity_dict["pressure"] = copy(self.pressure)
            
        # the temperature should be a property or None 
        if not (isinstance(self.temperature, Property) or self.temperature == None):
            self.ambiguity_dict["temperature"] = copy(self.temperature)
        
        # if stirring, stir_speed must be defined as property type
        if self.stir_speed == None:
            if self.stir == True:
                self.ambiguity_dict["stir_speed"] = "unknown"
        else:
            if not isinstance(self.stir_speed, Property): 
                self.ambiguity_dict["stir_speed"] = copy(self.stir_speed)
        
        # the duration should be property or None
        if not (isinstance(self.duration, Property) or self.duration == None):
            self.ambiguity_dict["duration"] = copy(self.duration)
            
        # update the attribute after giving the new value 
        for key, value in self.ambiguity_dict.items():
            new_property = ask_for_physical_property(key, value, mode = mode)
            if isinstance(new_property, Property):
                standardize_unit(None, key, new_property, property_type = key)
            setattr(self, key, new_property)
