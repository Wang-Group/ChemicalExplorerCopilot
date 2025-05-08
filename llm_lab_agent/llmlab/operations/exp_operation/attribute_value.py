from llmlab.operations.exp_operation.basic_step import BasicStep
from llmlab.utlis.property import Property
from typing import Union, Dict, Any
import re

RT_UNITS = ["room temperature", "RT.", "room_temperature"]

def parse_property(property: Union[Dict[str, Any], str, None])-> Union[Dict[str, Property], Property, str, None]:
    """
    Parse a general physical property and returns the representations
    """
    if isinstance(property, dict):
        if 'min' in property and 'max' in property:
            return {'min': Property(**property['min']),
                    'max': Property(**property['max'])}
        else:
            to_return = Property(**property)
            if (to_return.unit == None) and (to_return.quantity == None):
                return None
            else:
                return to_return
        
    elif isinstance(property, str):
        return property
        
    elif property == None:
        return None
    
    else:
        raise ValueError(f"the property ({property}) does not follow the desired format.")
    
def parse_pH(property: Union[Dict[str, Any], str, float, None])-> Union[Dict[str, Property], Property, str, None]:
    """
    Parse a general physical property and returns the representations
    """
    if isinstance(property, dict):
        if 'min' in property and 'max' in property:
            return {'min': float(property['min']),
                    'max': float(property['max'])}
        else:
            raise ValueError(f"the pH ({property}) does not follow the desired format.")
        
    elif isinstance(property, str):
        return property
        
    elif isinstance(property, float):
        return property
    
    elif isinstance(property, int):
        return float(property)
    
    elif property == None:
        return None
    
    else:
        raise ValueError(f"the property ({property}) does not follow the desired format.")

def parse_temperature(temperature: Union[Dict[str, Any], str, None]) -> Union[Dict[str, Property], Property, str, None]:
    """
    Parses the temperature input and returns an appropriate representation.

    Args:
        temperature: The temperature input which can be a dict with 'min' and 'max' keys for a range,
                     a dict with a single 'value' for a specific temperature, a descriptive string, or None.

    Returns:
        A dictionary with 'min' and 'max' keys containing Property objects for a range,
        a Property object for a specific temperature, a descriptive string, or None.
    """
    if isinstance(temperature, dict):
        if 'min' in temperature and 'max' in temperature:
            return {'min': Property(**temperature['min']),
                    'max': Property(**temperature['max'])}
        else:
            to_return = Property(**temperature)
            if (to_return.unit == None) and (to_return.quantity == None):
                return None
            else:
                return to_return
            
    elif isinstance(temperature, str):
        if temperature in RT_UNITS:
            return Property(quantity = 20.0, unit = "℃")
        else:
            return temperature
    elif temperature == None:
        return None
    else:
        raise ValueError(f"the temperature ({temperature}) does not follow desired format.")
