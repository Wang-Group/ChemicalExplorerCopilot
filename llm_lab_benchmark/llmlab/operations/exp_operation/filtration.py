from copy import copy
from typing import Union, Dict, Any
from llmlab.graph import exp_graph
from .attribute_value import *
from llmlab.utlis.property import Property, ChemicalNames, Solid
from llmlab.operations.exp_operation.basic_step import BasicStep
from llmlab.utlis.interactions import ask_for_physical_property, standardize_unit
class Filter(BasicStep):
    """
    Filter a mixture of solid and liquid.

    Args:
        reactor_name: str, mandatory
            The name of the reactor from the "Reactor" class, where the solution will be filtered.
        
        target_form: str, mandatory
            The form of the target product in the filtration process, which should be either "solid" or "liquid". If not given, default to null.
        
        filtrate_vessel: str, optional
            The vessel to send the liquid filtrate to. If not provided, the filtrate is sent to "waste". Defaults to null.
        
        stir: bool, optional
            Indicates if stirring should be applied during the process. Defaults to false.
        
        stir_speed: Union[Dict[str, Any], str, None], optional
            Represents the stirring intensity during the filtration, which can be in one of the following formats. Defaults to null if stir is not applied or the exact speed is not mentioned.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 500, "unit": "rpm"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 400, "unit": "rpm"}, "max": {"quantity": 800, "unit": "rpm"}}
            3. **Descriptive string**: A string describing the stirring intensity qualitatively (e.g., "vigorously", "gently", "softly").
        
        temperature: Union[Dict[str, Any], str, None], optional
            Represents the temperature or temperature range, or a descriptive string (e.g., "hot", "cool"), which can be in one of the following formats. If it is a specific value, follow the format from the "Property" class. Defaults to "{"quantity": 20.0, "unit": "℃"}".
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 25.0, "unit": "℃"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 20.0, "unit": "℃"}, "max": {"quantity": 30.0, "unit": "℃"}}
            3. **Descriptive string**: A string describing the temperature qualitatively (e.g., "warm", "hot").
        
        atmosphere: str, optional
            The environment to dry the solid. The value should be "vacuum", "inert", or "air". Defaults to "air". Use "inert" for drying the compound in N2 or Ar atmosphere.
    """
    
    def __init__(self, 
                 reactor_name: str, 
                 target_form: str = None,
                 filtrate_vessel: str = "waste",
                 stir: bool = False, 
                 stir_speed: Union[dict[float, str], str] = None,
                 temperature: dict = None,
                 atmosphere: str = "air"):
        
        super().__init__()
        
        self.reactor_name = str(reactor_name)
        self.target_form = str(target_form)
        self.filtrate_vessel = str(filtrate_vessel) if filtrate_vessel is not None else "waste"
        
        # define the stirring speed
        self.stir = bool(stir)
        self.stir_speed = parse_property(stir_speed)
        if self.stir == False and self.stir_speed != None:
            raise ValueError(f"The stir is off and the stiring speed ({self.stir_speed}) is defined!")
            
        if temperature is None:
            self.temperature = Property(quantity = 20, unit="℃")
        else:
            self.temperature = parse_temperature(temperature)
        
        self.atmosphere = str(atmosphere) if atmosphere is not None else "air"
    
    def check_ambiguity(self, mode = "plain_txt"):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        # find the potentially ambiguious quantity 
        self.ambiguity_dict = {}        
        if self.target_form == "liquid" or self.target_form == "solid":
            pass 
        else:
            self.ambiguity_dict["target_form"] = copy(self.target_form)
            
        # if stirring, stir_speed must be defined as property type
        if self.stir_speed == None:
            if self.stir == True:
                self.stir_speed = Property(quantity = 300, unit = "rpm")
        else:
            if not isinstance(self.stir_speed, Property): 
                self.ambiguity_dict["stir_speed"] = copy(self.stir_speed)
            
        # the temperature should be a property or None 
        if not (isinstance(self.temperature, Property) or self.temperature == None):
            self.ambiguity_dict["temperature"] = copy(self.temperature)
        
        # the atmosphere should be "vacuum", "inert", or "air"
        if self.atmosphere in ["vacuum", "inert", "air"] or self.atmosphere == None:
            pass 
        else:
            self.ambiguity_dict["atmosphere"] = copy(self.atmosphere)
            
        # update the attribute after giving the new value 
        for key, value in self.ambiguity_dict.items():
            new_property = ask_for_physical_property(key, value, mode = mode)
            if isinstance(new_property, Property):
                standardize_unit(None, key, new_property, property_type = key)
            setattr(self, key, new_property)
    
    def sim_execute(self, graph: exp_graph):
        """
        Simulate the filtration process. In this simplified version, we simply move everything to the filtrate vessel and left some unknown compound. 
        """
        # copy the content in the reactor
        content_temp = copy(graph.reactors[self.reactor_name].content)
        # add it to the filtrate_vessel 
        graph.reactors[self.filtrate_vessel].content = graph.reactors[self.filtrate_vessel].content + content_temp 
        # empty the original reactor and assign an unknown amount of solid to it 
        graph.reactors[self.reactor_name].content = [(Solid(identity = {"chemical_id": ["filtration_solid"]}), 
                                                      Property(quantity = 1e-5, unit="g"))]
        
        return
        
class Recrystallization(BasicStep):
    """
    Crystallization is the purification and separation process where a solute forms orderly crystals by altering solvent conditions.

    Args:
        reactor_name: str, mandatory
            The name of the vessel from the "Reactor" class where the recrystallization process will be performed.
        
        solvent: dict, mandatory
            A dictionary defining an object from the "ChemicalNames" class. optional. the solvent is used to control and accelerate the recrystallization process, seeding is a common solvent.

        high_temperature: Union[Dict[str, Any], str, None], optional
            Represents the high temperature used for recrystallization, following the "Property" format. If not mentioned exactly, default to null.
            Example: {"quantity": float, "unit": str}
            Example: {"quantity": 80.0, "unit": "℃"}
        
        low_temperature: Union[Dict[str, Any], str, None], optional
            Represents the low temperature used for recrystallization, following the "Property" format. If not mentioned exactly, default to null.
            Example: {"quantity": float, "unit": str}
            Example: {"quantity": 5.0, "unit": "℃"}
        
        repeat: int, optional
            The number of times the recrystallization process should be repeated. Defaults to 1.
    """

    def __init__(self,
                 reactor_name: str,
                 solvent: dict = None,
                 high_temperature: dict = None,
                 low_temperature: dict = None,
                 repeat: int = 1):
        
        super().__init__()
        
        self.reactor_name = str(reactor_name)
        self.solvent = ChemicalNames(**solvent) if solvent is not None else ChemicalNames(chemical_id=["water"])
        self.high_temperature = Property(**high_temperature) if high_temperature is not None else Property(quantity=None, unit=None)
        self.low_temperature = Property(**low_temperature) if low_temperature is not None else Property(quantity=20, unit="℃")
        self.repeat = int(repeat)
        
            
class Centrifuge(BasicStep):
    """
    Centrifuge to separate the mixture. Before the centrifuge process, the target material must be added or transferred to the centrifuge hardware.

    Args:
        centrifuge_reactor: str, mandatory
            The name of the reactor from the "Reactor" class where the centrifuge process will be conducted.
        
        target_chemical: dict, mandatory
            A dictionary defining an object from the "ChemicalNames" class, indicating the target materials in the centrifuge process.
        
        centrifuge_rate: Union[Dict[str, Any], str, None], mandatory
            Represents the rate of centrifuge, which can be in one of the following formats. If not mentioned exactly, default to null.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 250, "unit": "rpm"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 300, "unit": "rpm"}, "max": {"quantity": 30.0, "unit": "rpm"}}
            3. **Descriptive string**: A string describing the centrifuge rate qualitatively (e.g., "high speed", "low speed").
        
        centrifuge_time: Union[Dict[str, Any], str, None], optional
            Represents the time of centrifuge, which can be in one of the following formats. If not mentioned exactly, default to null.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 250, "unit": "hours"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 1, "unit": "days"}, "max": {"quantity": 2, "unit": "days"}}
            3. **Descriptive string**: A string describing the centrifuge time qualitatively.
    """
    
    def __init__(self,
                 centrifuge_reactor: str,
                 target_chemical: dict,
                 centrifuge_rate: dict = None,
                 centrifuge_time: dict = None
                 ):
        
        super().__init__()
        
        self.centrifuge_reactor = str(centrifuge_reactor)
        self.target_chemical = ChemicalNames(**target_chemical) if target_chemical is not None else None
        
        if centrifuge_rate is None:
            raise ValueError("the centrifuge rate can not be None!")
        else:
            self.centrifuge_rate = parse_property(centrifuge_rate)
        self.centrifuge_time = parse_property(centrifuge_time)
            
    def check_ambiguity(self, mode = "plain_txt"):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        # find the potentially ambiguious quantity 
        self.ambiguity_dict = {}        
        if not isinstance(self.centrifuge_rate, Property):
            self.ambiguity_dict["centrifuge_rate"] = copy(self.centrifuge_rate)
        if not isinstance(self.centrifuge_time, Property):
            self.ambiguity_dict["centrifuge_time"] = copy(self.centrifuge_time)
              
        # update the attribute after giving the new value 
        for key, value in self.ambiguity_dict.items():
            new_property = ask_for_physical_property(key, value, mode = mode)
            if isinstance(new_property, Property):
                standardize_unit(None, key, new_property, property_type = key)
            setattr(self, key, new_property)