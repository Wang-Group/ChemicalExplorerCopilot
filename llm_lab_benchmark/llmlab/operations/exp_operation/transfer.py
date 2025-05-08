from typing import Union
from .attribute_value import *
from llmlab.graph import exp_graph
from llmlab.utlis.property import Property
from llmlab.operations.exp_operation.basic_step import BasicStep

from copy import copy 
from llmlab.utlis.interactions import ask_for_physical_property, standardize_unit

class TransferLiquid(BasicStep):
    """
    Transfer the liquid from one reactor to another reactor.

    Args:
        from_reactor: str, mandatory
            The name of the reactor from the "Reactor" class, where the liquid will be withdrawn from.
        
        to_reactor: str, mandatory
            The name of the reactor from the "Reactor" class, where the liquid will be sent to.
        
        volume: Union[Dict[str, Any], str], mandatory
            Represents the volume of the transferred liquid, which can be in one of the following formats. Default to "all", indicating that all the liquid will be transferred.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 5.0, "unit": "mL"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 5.0, "unit": "mL"}, "max": {"quantity": 25.0, "unit": "mL"}}
            3. **Descriptive string**: The string "all" indicating that all the liquid will be transferred.

        stir: bool, optional
            Indicates if stirring should be applied during the addition. Default to false.
        
        stir_speed: Union[Dict[str, Any], str, None], optional
            Represents the stirring intensity when transferring the liquid into the to_reactor, which can be in one of the following formats. Default to "{"quantity": 300, "unit": "rpm"}" if the exact speed is not mentioned.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 500, "unit": "rpm"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 400, "unit": "rpm"}, "max": {"quantity": 800, "unit": "rpm"}}
            3. **Descriptive string**: A string describing the stirring intensity qualitatively (e.g., "vigorously", "gently", "softly").

        dropwise: bool, optional
            Indicates if the liquid is added dropwise. Default to false.
    """
    def __init__(self, 
                 from_reactor: str, 
                 to_reactor: str,
                 volume: Union[dict[float, str],str],
                 stir: bool = False,
                 stir_speed: str = None,
                 dropwise: bool = False):
        
        super().__init__()
        
        self.from_reactor = str(from_reactor)
        self.to_reactor = str(to_reactor)
        # read in the volume. if it is None, raise a value error.
        if volume is None:
            self.volume = None
            raise ValueError(f"the volume can not be None.")
        else:
            self.volume = parse_property(volume)

        self.dropwise = bool(dropwise)

        # define the stirring speed
        self.stir = bool(stir)
        self.stir_speed = parse_property(stir_speed)
        if self.stir == False and self.stir_speed != None:
            raise ValueError(f"The stir is off and the stiring speed ({self.stir_speed}) is defined!")
        
    def check_ambiguity(self, mode = "plain_txt"):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        # find the potentially ambiguious quantity 
        self.ambiguity_dict = {}
        if isinstance(self.volume, str):
            if self.volume != "all":
                self.ambiguity_dict["volume"] = copy(self.volume)
        elif not isinstance(self.volume, Property):
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
        Transfer certain amount of liquid to the vial
        """
        # get the amount of compounds inside the reactor
        self.volume_quantity = graph.reactors[self.from_reactor].total_amount()
        
        # if transfer all the content 
        if self.volume == "all":
            # record the actual physical objects we need to transfer, which should be used by the robot 
            # copy the whole content in the from_reactor
            content_temp = copy(graph.reactors[self.from_reactor].content)
            # empty the content from the from_reactor
            graph.reactors[self.from_reactor].content = []
            # take the content to the to_reactor
            graph.reactors[self.to_reactor].content = graph.reactors[self.to_reactor].content + content_temp 
            
        # transfer only part of the liquid 
        else:
            # check if the unit is consistent 
            if self.volume.unit == "mL":
                # calculate the percentage of the volume  
                percentage = self.volume.quantity/self.volume_quantity[0]
                # if it is larger than 1, get it to 1 
                if percentage > 1:
                    percentage = 1
                if percentage < 0:
                    percentage = 0 
                # iterate through all the chemicals in the from_reactor
                for chemical in graph.reactors[self.from_reactor].content:
                    # make a copy of the chemical 
                    temp = copy(chemical)
                    # calcualte how much of it is transferred to the to_reactor
                    temp[1].quantity = temp[1].quantity*percentage 
                    graph.reactors[self.to_reactor].content.append(temp)
                    # decrease the amount in the from_reactor
                    chemical[1].quantity = chemical[1].quantity * (1-percentage)
            else:
                raise ValueError(f"""the TransferLiquid step only supports volume with unit "mL"!""")
                    
        return
    
    def rescale(self, rescale_factor: float):
        """
        Apply rescale factor to the volume.
        """
        if self.volume == "all":
            self.volume_quantity[0] *= rescale_factor
            self.volume_quantity[1] *= rescale_factor
        else:
            self.volume.quantity *= rescale_factor
        
        
class TransferSolid(BasicStep):
    """
    Transfer the solid from one reactor to another reactor

    Args:
        from_reactor: str, mandatory
            The name of the reactor from the "Reactor" class, where the solid will be withdrawn from.
        
        to_reactor: str, mandatory
            The name of the reactor from the "Reactor" class, where the solid will be sent to.
        
        mass: Union[Dict[str, Any], str], mandatory
            Represents the quantity (i.e., mass) of the solid to be transferred, which can be in one of the following formats. Defaults to "all", indicating that all the solid will be transferred.
            1. **Single value**: A dictionary following the "Property" class format:
               {"quantity": float, "unit": str}
               Example: {"quantity": 5.0, "unit": "mg"}
            2. **Range**: A dictionary with min and max values, each following the "Property" class format:
               {"min": {"quantity": float, "unit": str}, "max": {"quantity": float, "unit": str}}
               Example: {"min": {"quantity": 5.0, "unit": "g"}, "max": {"quantity": 25.0, "unit": "g"}}
            3. **Descriptive string**: The string "all" indicating that all the solid will be transferred.
                    
    """
    def __init__(self, 
                 from_reactor: str, 
                 to_reactor: str,
                 mass: Union[dict[float, str],str]):
        
        super().__init__()
        
        self.from_reactor = str(from_reactor)
        self.to_reactor = str(to_reactor)
        # define the mass of the added component
        if mass is None:
            self.mass = None
            raise ValueError(f"the quantity can not be None.")
        else:
            self.mass = parse_property(mass)
    
    def check_ambiguity(self, mode = "plain_txt"):
        """
        Check each args for the function, and make sure they can be interpreted by the machine, otherwise ask the user for advice
        """
        # find the potentially ambiguious quantity 
        self.ambiguity_dict = {}        
        if isinstance(self.mass, str):
            if self.mass != "all":
                self.ambiguity_dict["quantity"] = copy(self.mass)
        elif not isinstance(self.mass, Property):
            self.ambiguity_dict["quantity"] = copy(self.mass)

        # update the attribute after giving the new value 
        for key, value in self.ambiguity_dict.items():
            new_property = ask_for_physical_property(key, value, mode = mode)
            if isinstance(new_property, Property):
                standardize_unit(None, key, new_property, property_type = key)
            setattr(self, key, new_property)

    def sim_execute(self, graph: exp_graph):
        """
        Transfer certain amount of solid to the vial
        """
        
        # record the actual physical objects we need to transfer, which should be used by the robot 
        self.mass_quantity = graph.reactors[self.from_reactor].total_amount()
        
        # if transfer all the content 
        if self.mass == "all":
            # copy the whole content in the from_reactor
            content_temp = copy(graph.reactors[self.from_reactor].content)
            # empty the content from the from_reactor
            graph.reactors[self.from_reactor].content = []
            # take the content to the to_reactor
            graph.reactors[self.to_reactor].content = graph.reactors[self.to_reactor].content + content_temp 
            
        # transfer only part of the liquid 
        else:
            # check if the unit is consistent 
            if self.mass.unit == "g":
                # calculate the percentage of the volume  
                percentage = self.mass.quantity/self.mass_quantity[1]
                # if it is larger than 1, get it to 1 
                if percentage > 1:
                    percentage = 1
                # iterate through all the chemicals in the from_reactor
                for chemical in graph.reactors[self.from_reactor].content:
                    # make a copy of the chemical 
                    temp = copy(chemical)
                    # calcualte how much of it is transferred to the to_reactor
                    temp[1].quantity = temp[1].quantity*percentage 
                    graph.reactors[self.to_reactor].content.append(temp)
                    # decrease the amount in the from_reactor
                    chemical[1].quantity = chemical[1].quantity * (1-percentage)
            else:
                raise ValueError(f"""the TransferSolid step only supports mass with unit "g"!""")
            
        return
    
    def rescale(self, rescale_factor: float):
        """
        Apply rescale factor to the mass.
        """
        if self.mass == "all":
            self.mass_quantity[0] *= rescale_factor
            self.mass_quantity[1] *= rescale_factor
        else:
            self.mass.quantity *= rescale_factor