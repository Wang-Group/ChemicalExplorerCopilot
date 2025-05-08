from llmlab.graph import exp_graph
from llmlab.utlis.property import Property, Liquid, Solid
from llmlab.operations.exp_operation.basic_step import BasicStep
from typing import Union
from .attribute_value import *
from copy import copy 
from llmlab.utlis.interactions import ask_for_physical_property, standardize_unit

class WashSolid(BasicStep):
    """
    Wash solid by adding solvent and filtering.

    Args:
        reactor_name: str, mandatory
            The name of the vessel from the "Reactor" class containing the solid to wash.
        
        solvent: dict, mandatory
            A dictionary defining an object from the "Liquid" class, including the information of the solvent that will be used to wash the solid.
        
        solvent_temperature: Union[Dict[str, Any], str, None], optional
            Represents the temperature of the solvent, which can be in one of the following formats. Defaults to null.
            1. **Single value**: A dictionary following the "Property" format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 20.0, "unit": "℃"}
            2. **Range**: A dictionary with min and max values, each following the "Property" format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 18.0, "unit": "℃"}, "max": {"quantity": 22.0, "unit": "℃"}}
            3. **Descriptive string**: A string describing the temperature qualitatively (e.g., "warm").
        
        volume: Union[Dict[str, Any], str], mandatory
            Represents the volume of the added solvent, which can be in one of the following formats.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 5.0, "unit": "mL"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 5.0, "unit": "mL"}, "max": {"quantity": 25.0, "unit": "mL"}}
            3. **Descriptive string**: The string "all" indicating that all the liquid will be transferred.
        
        waste_vessel: str, optional
            The vessel to send the waste solution to. If not provided, the waste is sent to waste. Defaults to null.
        
        stir: bool, optional
            Indicates if stirring should be applied during the addition. Defaults to false.
        
        stir_speed: Union[Dict[str, Any], str, None], optional
            Represents the stirring intensity during the washing process, which can be in one of the following formats. It should be null if stir is not applied or the exact speed is not mentioned. Defaults to null.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 500, "unit": "rpm"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 400, "unit": "rpm"}, "max": {"quantity": 800, "unit": "rpm"}}
            3. **Descriptive string**: A string describing the stirring intensity qualitatively (e.g., "vigorously", "gently", "softly").
        
        atmosphere: str, optional
            The environment to dry the solid. The value should be "vacuum", "inert", or "air". Defaults to "air". Use "inert" for drying the compound in N2 or Ar atmosphere.
        
        repeat: int, optional
            The number of wash cycles to perform. Defaults to 1.
    """
    
    def __init__(self,
                 reactor_name: str, 
                 solvent: dict,
                 volume: Union[dict[float, str], str],
                 solvent_temperature: dict = None,
                 waste_vessel: str = None,
                 stir: bool = False,
                 stir_speed: Union[dict[float, str], str] = None,
                 atmosphere: str = "air",
                 repeat: int = 1):
        
        super().__init__()
        
        self.reactor_name = str(reactor_name)
        self.solvent = Liquid(**solvent)
        self.solvent_temperature = parse_temperature(solvent_temperature)
        
        # read in the volume quantity
        self.volume = parse_property(volume)
        # read in the filtrate waste_vessel
        self.waste_vessel = str(waste_vessel) if waste_vessel is not None else "waste"
        
        # define the stirring speed
        self.stir = bool(stir)
        self.stir_speed = parse_property(stir_speed)
        if self.stir == False and self.stir_speed != None:
            raise ValueError(f"The stir is off and the stiring speed ({self.stir_speed}) is defined!")
            
        self.atmosphere = str(atmosphere) if atmosphere is not None else "air"
        self.repeat = int(repeat) if repeat is not None else 1
                
    def check_ambiguity(self, mode = "plain_txt"):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        # find the potentially ambiguious quantity 
        self.ambiguity_dict = {}
        
        # the volume should be a specific value 
        if not isinstance(self.volume, Property):
            self.ambiguity_dict["volume"] = copy(self.volume)
            
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
            
    def sim_execute(self, graph: exp_graph):
        """
        1. make sure the quantity is not ambiguinous before running any execution
        """
        for i in range(self.repeat):
            graph.reactors[self.waste_vessel].content.append(
                (self.solvent, self.volume)
            )
            
    def rescale(self, rescale_factor: float):
        """
        Apply rescale factor to the mass
        """
        self.volume.quantity *= rescale_factor
        
        return [self.solvent, self.volume.quantity*self.repeat]
    
class Dry(BasicStep):
    """
    Dry solid.

    Args:
        reactor_name: str, mandatory
            The name of the vessel from the "Reactor" class containing the solid to dry.
        
        time: Union[Dict[str, Any], str, None], optional
            Represents the time to dry the solid, which can be in one of the following formats. Defaults to null if not mentioned.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 2.0, "unit": "hours"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 1.0, "unit": "hours"}, "max": {"quantity": 3.0, "unit": "hours"}}
            3. **Descriptive string**: A string describing the duration qualitatively.
        
        temperature: Union[Dict[str, Any], str, None], optional
            Represents the temperature to dry the solid, which can be in one of the following formats. If not mentioned exactly, default to "{"quantity": 20.0, "unit": "℃"}"
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 40.0, "unit": "℃"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 35.0, "unit": "℃"}, "max": {"quantity": 45.0, "unit": "℃"}}
            3. **Descriptive string**: A string describing the temperature qualitatively (e.g., "room temperature").
        
        atmosphere: str, optional
            The environment to dry the solid. The value should be "vacuum", "inert", or "air". Defaults to "air". Use "inert" for drying the compound in N2 or Ar atmosphere.
    """

    def __init__(self,
                 reactor_name: str,
                 time: dict = None,
                 temperature: dict = None,
                 atmosphere: str = "air"):
        
        super().__init__()
        
        self.reactor_name = str(reactor_name)
        # read in the drying time
        if time is None:
            self.time = Property(quantity = 15, unit = "minute")
        else:
            self.time = parse_property(time)
        # read in the temperature
        if temperature is None:
            self.temperature = Property(quantity = 20, unit="℃")
        else:
            self.temperature = parse_temperature(temperature)
        # read in the atmosphere
        self.atmosphere = str(atmosphere) if atmosphere is not None else "air"

class Precipitate(BasicStep):
    """
    Precipitation refers to the formation of insoluble solid material in a solvent due to a chemical reaction.

    Args:
        reactor_name: str, mandatory
            The name of the vessel from the "Reactor" class, to heat/chill and stir to cause precipitation.
        
        temperature: Union[Dict[str, Any], str, None], optional
            Represents the temperature to heat/chill the reactor to, which can be in one of the following formats. Defaults to "{"quantity": 20.0, "unit": "℃"}".
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 25.0, "unit": "℃"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 20.0, "unit": "℃"}, "max": {"quantity": 30.0, "unit": "℃"}}
            3. **Descriptive string**: A string describing the temperature qualitatively.
        
        stirring_time: Union[Dict[str, Any], str, None], optional
            Represents the time to stir the vessel at a given temperature, which can be in one of the following formats. Defaults to null.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 2.0, "unit": "hours"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 1.0, "unit": "hours"}, "max": {"quantity": 3.0, "unit": "hours"}}
            3. **Descriptive string**: A string describing the duration qualitatively.
        
        stir_speed: Union[Dict[str, Any], str, None], optional
            Represents the stirring intensity or precise stirring speed, which can be in one of the following formats. It should be null if stir is not applied or the exact speed is not mentioned. Default to null.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 500, "unit": "rpm"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 400, "unit": "rpm"}, "max": {"quantity": 800, "unit": "rpm"}}
            3. **Descriptive string**: A string describing the stirring intensity qualitatively (e.g., "vigorously", "gently", "softly").
        
        reagent: dict, optional
            A dictionary defining an object from either the "Liquid" or "Solid" class, representing an optional reagent to add to trigger precipitation. Defaults to null.
        
        reagent_quantity: Union[Dict[str, Any], str, None], optional
            Represents the quantity (e.g., volume or mass) of the reagent to add to trigger precipitation, which can be in one of the following formats. This argument should be used if reagent is not null. Defaults to null.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: 
                    {"quantity": 5.0, "unit": "g"}
                    {"quantity": 3.0, "unit": "mL"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: 
                    {"min": {"quantity": 3.0, "unit": "mL"}, "max": {"quantity": 7.0, "unit": "mL"}}
                    {"min": {"quantity": 4.0, "unit": "g"}, "max": {"quantity": 5.0, "unit": "g"}}
            3. **Descriptive string**: A string describing the quantity qualitatively (e.g., "small amount", "large amount").
        
        repeat: int, optional
            Indicates the number of times to repeat the precipitation process. Defaults to 1.
    """
    
    def __init__(self,
                 reactor_name: str, 
                 temperature: dict = None,
                 stirring_time: dict = None,
                 stir_speed: Union[dict[float, str], str] = None,
                 reagent: dict = None,
                 reagent_quantity: dict = None,
                 repeat: int = 1):
        
        super().__init__()
        
        self.reactor_name = str(reactor_name)
        
        # read in the temperature
        if temperature is None:
            self.temperature = Property(quantity = 20, unit="℃")
        else:
            self.temperature = parse_temperature(temperature)
            
        self.stirring_time = parse_property(stirring_time)
        
        # define the stirring speed
        self.stir_speed = parse_property(stir_speed)

        # define the reagent
        if reagent is not None:
            try:
                self.reagent = Liquid(**reagent)
            except:
                self.reagent = Solid(**reagent)
        else:
            self.reagent = None
            
        self.reagent_quantity = parse_property(reagent_quantity)
        if (self.reagent is not None) and (self.reagent_quantity is None):
            raise ValueError(f"""The reagent quantity must be declared if a reagent is going to be used.""")
        
        self.repeat = int(repeat) if repeat is not None else 1
        
    def sim_execute(self, graph: exp_graph):
        """
        1. make sure the quantity is not ambiguinous before running any execution
        """
        if self.reagent is not None:
            for i in range(self.repeat):
                graph.reactors[self.reactor_name].content.append(
                    (self.reagent, self.reagent_quantity)
                )
                
    def check_ambiguity(self, mode = "plain_txt"):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        # find the potentially ambiguious quantity 
        self.ambiguity_dict = {}
        
        # the reagent_quantity should be a specific value 
        if not isinstance(self.reagent_quantity, Property):
            self.ambiguity_dict["reagent_quantity"] = copy(self.reagent_quantity)
            
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
            
    def rescale(self, rescale_factor: float):
        """
        Apply rescale factor to the mass
        """
        if self.reagent is not None:
            self.reagent_quantity.quantity *= rescale_factor
            return [self.reagent, self.reagent_quantity.quantity*self.repeat]