from .basic_step import BasicStep
from llmlab.utlis.property import Property, Liquid
from llmlab.operations.exp_operation.attribute_value import parse_property, parse_pH
from typing import Union, Dict, Any, Optional, List
import typing

from copy import copy 
from llmlab.utlis.interactions import ask_for_physical_property, standardize_unit

class AdjustpH(BasicStep):
    """
    Adjust the pH of a solution inside a reactor.

    Args:
        reactor_name: str, mandatory
            The name of the reactor from the "Reactor" class, where the pH will be adjusted.
        
        pH: Union[Dict[str, Any], str, float], mandatory
            Represents the target pH value to be adjusted, which can be in one of the following formats:
            1. **Single value**: A float representing a specific pH value.
               Example: 4.5
            2. **Range**: A dictionary with min and max values:
               {"min": float, "max": float}
               Example: {"min": 3.5, "max": 4.8}
            3. **Descriptive string**: A string describing the pH qualitatively (e.g., "acidic", "neutral").
        
        stir: bool, optional
            Indicates if stirring should be applied during the process. Defaults to true.
        
        stir_speed: Union[Dict[str, Any], str, None], optional
            Represents the stirring intensity when adjusting the pH, which can be in one of the following formats. Defaults to null if not mentioned.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 500, "unit": "rpm"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 400, "unit": "rpm"}, "max": {"quantity": 800, "unit": "rpm"}}
            3. **Descriptive string**: A string describing the stirring intensity qualitatively (e.g., "vigorously", "gently", "softly").
        
        acid_reagent: dict, optional
            A dictionary defining an object from the "Liquid" class, including the information of the acid solution that will be used in tuning the pH value. Defaults to null.
        
        base_reagent: dict, optional
            A dictionary defining an object from the "Liquid" class, including the information of the base solution that will be used in tuning the pH value. Defaults to null.
    """
    def __init__(self, 
                 reactor_name: str,
                 pH: Union[dict[float, str], str, float],
                 stir: bool = True, 
                 stir_speed: Union[dict[float, str], str] = None,
                 acid_reagent: Liquid = None,
                 base_reagent: Liquid = None):
        
        super().__init__()
        self.reactor_name = str(reactor_name)
        self.pH = parse_pH(pH) # Use parse_pH to interpret the pH value or range
        
        # define the stirring speed
        self.stir = bool(stir)
        self.stir_speed = parse_property(stir_speed)
        if self.stir == False and self.stir_speed != None:
            raise ValueError(f"The stir is off and the stiring speed ({self.stir_speed}) is defined!")
            
        self.acid_reagent = Liquid(**acid_reagent) if acid_reagent is not None else Liquid(identity = None, concentration = None, solvent = None)
        self.base_reagent = Liquid(**base_reagent) if base_reagent is not None else Liquid(identity = None, concentration = None, solvent = None)
        
    def check_ambiguity(self):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        # find the potentially ambiguious quantity 
        self.ambiguity_dict = {}
        
        # the pH can be either float or None 
        if not (isinstance(self.pH, float) or self.pH == None):
            self.ambiguity_dict["pH"] = copy(self.pH)
            
        # if stirring, stir_speed must be defined as property type
        if self.stir_speed == None:
            if self.stir == True:
                self.ambiguity_dict["stir_speed"] = "unknown"
        else:
            if not isinstance(self.stir_speed, Property): 
                self.ambiguity_dict["stir_speed"] = copy(self.stir_speed)
            
        # update the attribute after giving the new value 
        for key in self.ambiguity_dict.keys():
            value = self.ambiguity_dict[key]
            new_property = ask_for_physical_property(key, value, mode = "plain_txt")
            if isinstance(new_property, Property):
                standardize_unit(None, key, new_property, property_type = key)
            setattr(self, key, new_property)