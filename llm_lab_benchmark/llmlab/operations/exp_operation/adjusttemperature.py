from llmlab.operations.exp_operation.basic_step import BasicStep
from llmlab.utlis.property import Property
from typing import Union, Dict, Any
import re
from .attribute_value import *

from copy import copy 
from llmlab.utlis.interactions import ask_for_physical_property, standardize_unit

class AdjustTemperatureTo(BasicStep):
    """
    Adjust the reactor's temperature to the specified target temperature. The rate of temperature adjustment can be specified through ramp_rate. If ramp_rate is not provided, no specific adjustment rate will be applied.

    Args:
        reactor_name: str, mandatory
            The name of the reactor from the "Reactor" class.
        
        temperature: Union[Dict[str, Any], str], mandatory
            Represents the target temperature, temperature range, or a descriptive string (e.g., "hot", "cool"), which can be in one of the following formats. If it is a specific value, follow the format from the "Property" class:
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 75.0, "unit": "℃"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 70.0, "unit": "℃"}, "max": {"quantity": 80.0, "unit": "℃"}}
            3. **Descriptive string**: A string describing the temperature qualitatively (e.g., "hot", "cool").
        
        adjust_method: str, optional
            Method to adjust the temperature (e.g., water bath, oil bath). Defaults to null.
        
        stir: bool, optional
            Indicates if stirring should be applied during the process. Defaults to false.
        
        stir_speed: Union[Dict[str, Any], str, None], optional
            Represents the stirring intensity when adjusting the temperature, which can be in one of the following formats. Defaults to null if not mentioned.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 500, "unit": "rpm"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 400, "unit": "rpm"}, "max": {"quantity": 800, "unit": "rpm"}}
            3. **Descriptive string**: A string describing the stirring intensity qualitatively (e.g., "vigorously", "gently", "softly").
        
        ramp_rate: Union[Dict[str, Any], str, None], optional
            Represents the rate of heating or cooling, which can be in one of the following formats. If not provided, no specific rate is applied.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 25.0, "unit": "℃/h"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 20.0, "unit": "℃/h"}, "max": {"quantity": 30.0, "unit": "℃/h"}}
            3. **Descriptive string**: A string describing the rate qualitatively (e.g., "slowly", "rapidly").
    """

    
    def __init__(self,
                 reactor_name: str,
                 temperature: Union[dict, str, None],
                 adjust_method: str = None,
                 stir: bool = False,
                 stir_speed: Union[dict[float, str], str] = None,
                 ramp_rate: Union[dict, None] = None):
        super().__init__()
        
        self.reactor_name = str(reactor_name)
        
        # Parse temperature to handle dict, descriptive string, or leave it undefined
        if temperature == None:
            raise ValueError(f"the temperature can not be None.")
        else:
            self.temperature = parse_temperature(temperature)

        self.adjust_method = str(adjust_method) if adjust_method is not None else None
        
        # define the stirring speed
        self.stir = bool(stir)
        self.stir_speed = parse_property(stir_speed)
        if self.stir == False and self.stir_speed != None:
            raise ValueError(f"The stir is off and the stiring speed ({self.stir_speed}) is defined!")
            
        self.ramp_rate = parse_property(ramp_rate)
    
    def check_ambiguity(self):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        # find the potentially ambiguious quantity 
        self.ambiguity_dict = {}
        
        # the temperature should be a property
        if not isinstance(self.temperature, Property):
            self.ambiguity_dict["temperature"] = copy(self.temperature)
        
        # if stirring, stir_speed must be defined as property type
        if self.stir_speed == None:
            if self.stir == True:
                self.stir_speed = Property(quantity = 300, unit = "rpm")
        else:
            if not isinstance(self.stir_speed, Property): 
                self.ambiguity_dict["stir_speed"] = copy(self.stir_speed)

        # update the attribute after giving the new value 
        for key, value in self.ambiguity_dict.items():
            new_property = ask_for_physical_property(key, value, mode = "plain_txt")
            if isinstance(new_property, Property):
                standardize_unit(None, key, new_property, property_type = key)
            setattr(self, key, new_property)
            
class AdjustTemperatureForDuration(BasicStep):
    """
    Maintain the reactor's temperature at a specified value or range for a certain duration. The rate of temperature adjustment can be specified through ramp_rate. If ramp_rate is not provided, no specific adjustment rate is applied.

    Args:
        reactor_name: str, mandatory
            The name of the reactor from the "Reactor" class.
        
        temperature: Union[Dict[str, Any], str], mandatory
            Represents the target temperature, temperature range, or a descriptive string (e.g., "hot", "cool"), which can be in one of the following formats. If it is a specific value, follow the format from the "Property" class:
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 75.0, "unit": "℃"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 70.0, "unit": "℃"}, "max": {"quantity": 80.0, "unit": "℃"}}
            3. **Descriptive string**: A string describing the temperature qualitatively (e.g., "hot", "cool").
        
        duration: Union[Dict[str, Any], str], mandatory
            Represents the time period for maintaining the temperature, which can be in one of the following formats. Defaults to null if duration is not mentioned.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 2.0, "unit": "days"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 1.0, "unit": "hours"}, "max": {"quantity": 3.0, "unit": "hours"}}
            3. **Descriptive string**: A string describing the duration qualitatively.
        
        adjust_method: str, optional
            Method to adjust the temperature (e.g., water bath, oil bath). Defaults to null.
        
        stir: bool, optional
            Indicates if stirring should be applied during the process. Defaults to false.
        
        stir_speed: Union[Dict[str, Any], str, None], optional
            Represents the stirring intensity when maintaining the temperature, which can be in one of the following formats. Defaults to null if not mentioned.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 500, "unit": "rpm"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 400, "unit": "rpm"}, "max": {"quantity": 800, "unit": "rpm"}}
            3. **Descriptive string**: A string describing the stirring intensity qualitatively (e.g., "vigorously", "gently", "softly").
        
        ramp_rate: Union[Dict[str, Any], str, None], optional
            Represents the rate of heating or cooling, which can be in one of the following formats. If not provided, no specific rate is applied.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 25.0, "unit": "℃/min"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 20.0, "unit": "℃/h"}, "max": {"quantity": 30.0, "unit": "℃/h"}}
            3. **Descriptive string**: A string describing the rate qualitatively (e.g., "slowly", "rapidly").
        
        reflux: bool, optional
            Indicates if reflux is applied when in the temperature maintaining process. Defaults to null.
    """

    def __init__(self,
                 reactor_name: str,
                 temperature: Union[dict, str, None],
                 duration: dict,
                 adjust_method: str = None,
                 stir: bool = False,
                 stir_speed: Union[dict[float, str], str] = None,
                 ramp_rate: Union[dict, None] = None,
                 reflux: bool = False):
        super().__init__()
        
        self.reactor_name = reactor_name
        if temperature is None:
            raise ValueError(f"the temperature can not be None.")
        else:
            self.temperature = parse_temperature(temperature)
        
        if duration is None:
            raise ValueError(f"the duration can not be None.")
        else:
            self.duration = parse_property(duration)
        
        self.adjust_method = str(adjust_method) if adjust_method is not None else None
        
        # define the stirring speed
        self.stir = bool(stir)
        self.stir_speed = parse_property(stir_speed)
        if self.stir == False and self.stir_speed != None:
            raise ValueError(f"The stir is off and the stiring speed ({self.stir_speed}) is defined!")
            
        self.ramp_rate = parse_property(ramp_rate)
        self.reflux = bool(reflux)
    
    def check_ambiguity(self, mode = "plain_txt"):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        # find the potentially ambiguious quantity 
        self.ambiguity_dict = {}     
        
        # the temperature should be a specific value 
        if not isinstance(self.temperature, Property):
            self.ambiguity_dict["temperature"] = copy(self.temperature)
        
        # the time should be a specific value
        if not isinstance(self.duration, Property):
            self.ambiguity_dict["duration"] = copy(self.duration)
            
        # if stirring, stir_speed must be defined as property type
        if self.stir_speed == None:
            if self.stir == True:
                self.stir_speed = Property(quantity = 300, unit = "rpm")
        else:
            if not isinstance(self.stir_speed, Property): 
                self.ambiguity_dict["stir_speed"] = copy(self.stir_speed)
            
        # update the attribute after giving the new value 
        for key, value in self.ambiguity_dict.items():
            new_property = ask_for_physical_property(key, value, mode = mode)
            if isinstance(new_property, Property):
                standardize_unit(None, key, new_property, property_type = key)
            setattr(self, key, new_property)