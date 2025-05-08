from llmlab.graph import exp_graph
from llmlab.utlis.property import Property, Liquid, Solid
from llmlab.operations.exp_operation.basic_step import BasicStep
from typing import Union, Dict, Any
from llmlab.operations.exp_operation.attribute_value import parse_property, parse_pH
from copy import copy 
from llmlab.utlis.interactions import ask_for_physical_property, standardize_unit

class AddLiquid(BasicStep):
    """
    Add a liquid to a reactor.
    Args:
        reactor_name: str, mandatory
            The name of the reactor from the "Reactor" class, where the liquid will be added.
        
        liquid: dict, mandatory
            A dictionary defining an object from the "Liquid" class, including the information of the liquid that will be added.
        
        liquid_temperature: Union[Dict[str, Any], str, None], optional
            Represents the temperature of the added liquid, which can be in one of the following formats:
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 5.0, "unit": "℃"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 5.0, "unit": "℃"}, "max": {"quantity": 25.0, "unit": "℃"}}
            3. **Descriptive string**: A string describing the temperature qualitatively.
        
        volume: Union[Dict[str, Any], str], mandatory
            Represents the volume of the added liquid, which can be in one of the following formats:
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 5.0, "unit": "mL"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 5.0, "unit": "mL"}, "max": {"quantity": 25.0, "unit": "mL"}}
            3. **Descriptive string**: A string describing the volume qualitatively (e.g., "appropriate", "minimum amount", "maximum amount").
        
        pH: Union[Dict[str, Any], str, float, None], optional
            Represents the pH value of the liquid, which can be in one of the following formats:
            1. **Range**: A dictionary with min and max values:
               {"min": float, "max": float}
               Example: {"min": 3.5, "max": 4.8}
            2. **Single value**: A float value representing a specific pH.
               Example: 4.5
            3. **Descriptive string**: A string describing the pH qualitatively (e.g., "acidic", "neutral").
        
        dropwise: bool, optional
            Indicates if the liquid is added dropwise. Defaults to false.
        
        stir: bool, optional
            Indicates if stirring should be applied during the addition. Defaults to false.
        
        stir_speed: Union[Dict[str, Any], str, None], optional
            Represents the stirring intensity when adding the liquid into the reactor, which can be in one of the following formats. Defaults to 300 rpm if the exact speed is not mentioned.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 500, "unit": "rpm"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 400, "unit": "rpm"}, "max": {"quantity": 800, "unit": "rpm"}}
            3. **Descriptive string**: A string describing the stirring intensity qualitatively (e.g., "vigorously", "gently", "softly").
    """
    def __init__(self,
                 reactor_name: str, 
                 liquid: dict,
                 volume: Union[dict[float, str], str],
                 liquid_temperature: Union[Dict[str, Any], str, float, None] = None,
                 pH: Union[Dict[str, Any], str, float, None] = None,
                 dropwise: bool = False,
                 stir: bool = False,
                 stir_speed: Union[Dict[str, Any], str, float, None] = None):
        
        super().__init__()
        
        # read in the reactor name and the liquid
        self.reactor_name = str(reactor_name)
        self.liquid = Liquid(**liquid)
        
        # read in the volume. if it is None, raise a value error.
        if volume:
            self.volume = parse_property(volume)
        else:
            self.volume = None
            raise ValueError(f"the volume can not be None.")

        # read in the liquid temperature (by default, it is None)
        self.liquid_temperature = parse_property(liquid_temperature)
        self.pH = parse_pH(pH)
        
        # define the stirring speed
        self.stir = bool(stir)
        self.stir_speed = parse_property(stir_speed)
        if self.stir == False and self.stir_speed != None:
            raise ValueError(f"The stir is off and the stiring speed ({self.stir_speed}) is defined!")

        # check if the liquid is added dropwise
        self.dropwise = bool(dropwise)

    def check_ambiguity(self):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        # find the potentially ambiguious quantity 
        self.ambiguity_dict = {}
        
        # the volume must be a property type 
        if not isinstance(self.volume, Property):
            self.ambiguity_dict["volume"] = copy(self.volume)
            
        # if the liquid temperature is not a Property or None, we need to ask about it as well 
        if not (isinstance(self.liquid_temperature, Property) or self.liquid_temperature == None):
            self.ambiguity_dict["liquid_temperature"] = copy(self.liquid_temperature)
            
        # the pH can be either float or None 
        if not (isinstance(self.pH, float) or self.pH == None):
            self.ambiguity_dict["pH"] = copy(self.pH)
            
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

    def sim_execute(self, graph: exp_graph):
        """
        1. make sure the quantity is not ambiguinous before running any execution
        """
        graph.reactors[self.reactor_name].content.append(
            (self.liquid, self.volume)
        )
    
    def rescale(self, rescale_factor: float):
        """
        Apply rescale factor to the mass
        """
        if self.volume.unit != "mL":
            raise ValueError("the unit should be mL by now!")
        
        self.volume.quantity *= rescale_factor
        
        return [self.liquid, self.volume.quantity]
        
class AddSolid(BasicStep):
    """
    Add a solid to a reactor.

    Args:
        reactor_name: str, mandatory
            The name of the reactor from the "Reactor" class, where the solid will be added.
        
        solid: dict, mandatory
            A dictionary defining an object from the "Solid" class, including the information of the solid that will be added.
        
        mass: Union[Dict[str, Any], str], mandatory
            Represents the mass quantity of the solid to be added, which can be in one of the following formats:
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               The "unit" must represent a unit of mass only (e.g., "mg", "g", "kg") and should not include units of concentration (e.g., "mg/mL", "g/L", "mol/L").
               Example: {"quantity": 10, "unit": "mg"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               The "unit" must represent a unit of mass only (e.g., "mg", "g", "kg") and should not include units of concentration (e.g., "mg/mL", "g/L", "mol/L").
               Example: {"min": {"quantity": 5.0, "unit": "mg"}, "max": {"quantity": 20.0, "unit": "mg"}}
            3. **Descriptive string**: A string describing the quantity qualitatively (e.g., "appropriate", "minimum amount", "maximum amount").
            
            Units like "mg/mL", "g/L", "mol/L" are not acceptable for mass quantity and should be treated as concentration units.
        
        stir: bool, optional
            Indicates if stirring should be applied during the addition. Defaults to false.
        
        stir_speed: Union[Dict[str, Any], str, None], optional
            Represents the stirring intensity when adding the solid into the reactor, which can be in one of the following formats. Defaults to null if not mentioned.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 500, "unit": "rpm"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 400, "unit": "rpm"}, "max": {"quantity": 800, "unit": "rpm"}}
            3. **Descriptive string**: A string describing the stirring intensity qualitatively (e.g., "vigorously", "gently", "softly").
    """
    def __init__(self,
                 reactor_name: str, 
                 solid: dict,
                 mass: Union[dict[float, str], str],
                 stir: bool = False,
                 stir_speed: str = None):
        super().__init__()
        # read in the mandatory properties 
        self.reactor_name = str(reactor_name)
        self.solid = Solid(**solid)
        
        # read in the mass quantity. if it is None, raise a value error.
        if mass:
            self.mass = parse_property(mass)
        else:
            self.mass = None
            raise ValueError(f"the quantity can not be None.")

        # define the stirring speed
        self.stir = bool(stir)
        self.stir_speed = parse_property(stir_speed)
        if self.stir == False and self.stir_speed != None:
            raise ValueError(f"The stir is off and the stiring speed ({self.stir_speed}) is defined!")
            
    def check_ambiguity(self):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        # find the potentially ambiguious quantity 
        self.ambiguity_dict = {}
        if not isinstance(self.mass, Property):
            self.ambiguity_dict["quantity"] = copy(self.mass)
            
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
        
    def sim_execute(self, graph: exp_graph):
        """
        1. make sure the quantity is not ambiguinous before running any execution
        """
        graph.reactors[self.reactor_name].content.append(
            (self.solid, self.mass)
        )
        
    def rescale(self, rescale_factor: float):
        """
        Apply rescale factor to the mass
        """
        if self.mass.unit != "g":
            raise ValueError("the unit should be g by now!")
        
        self.mass.quantity *= rescale_factor
        
        return [self.solid, self.mass.quantity]