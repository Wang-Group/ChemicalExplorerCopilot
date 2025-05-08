from pydantic import BaseModel, ConfigDict, field_validator
import typing
from typing import Union
import llmlab 
import re 
from typing import Dict, Any, List
import inspect
import warnings

def replace_empty_arrays(data):
    if isinstance(data, list):
        return [replace_empty_arrays(item) for item in data] if data else None
    elif isinstance(data, dict):
        return {key: replace_empty_arrays(value) for key, value in data.items()}
    return data

def get_dict_from_object(obj):
    if isinstance(obj, BaseModel):
        args = list(obj.__fields__.keys())
    else:
        signature = inspect.signature(type(obj).__init__)
        args = [param.name for param in signature.parameters.values()][1:]
    
    if isinstance(obj, dict):
        return {k: get_dict_from_object(v) for k, v in obj.items()}
    elif hasattr(obj, "__dict__"):
        return {k: get_dict_from_object(v) for k, v in obj.__dict__.items() if k in args}
    elif isinstance(obj, list):
        return [get_dict_from_object(i) for i in obj]
    else:
        return obj
    
def get_min_max_values(D: Dict[Any, Any]) -> List[Any]:
    result = []
    if "min" in D:
        result.append(D["min"])
    if "max" in D:
        result.append(D["max"])
    return result
       
class Reactor(BaseModel):
    """
    A class defines the reactor.
    Args:
        reactor_name: str type. the name of the reactor. Each individual solid or liquid, unless otherwise stated should be contained within their own reactorss.
        maximum_volume: float type. the maximum volume of a reactor in mL. 
    """
    model_config = ConfigDict(extra="forbid")
    
    reactor_name: typing.Optional[str]
    maximum_volume: typing.Optional[float] = 10 
    content: typing.Optional[list] = []

    def total_amount(self):
        """
        Calcualte the amount of liquid in mL and the amount of solid in g. 
        Returns:
            Tuple: (amount of liquid, amount of solid)
        """
        liquid_amount = 0
        solid_amount = 0
        for chemical in self.content:
            if isinstance(chemical[0],Liquid): 
                if chemical[1].unit == "mL":
                    liquid_amount = liquid_amount + chemical[1].quantity 
                else:
                    raise ValueError(f"""the volume unit of the liquid should be "mL".""")
            elif isinstance(chemical[0], Solid):
                if chemical[1].unit == "g":
                    solid_amount = solid_amount + chemical[1].quantity 
                else:
                    raise ValueError(f"""the mass unit of the solid should be "g".""")
            else:
                raise ValueError(f"""the chemical should be Solid or Liquid type. Current type is {type(chemical[0])}""")
            
        return [liquid_amount, solid_amount]

    def remove_volume(self, volume):
        self.current_volume -= volume
        if self.current_volume < 0:
            self.current_volume = 0

    def remove_mass(self, mass):
        self.current_mass -= mass
        if self.current_mass < 0:
            self.current_mass = 0

    def check_capacity(self, max_volume, max_mass):
        if self.current_volume > max_volume:
            raise ValueError(f"Reactor {self.reactor_name} exceeded its maximum volume capacity.")
        if self.current_mass > max_mass:
            raise ValueError(f"Reactor {self.reactor_name} exceeded its maximum mass capacity.")

    def to_dict(self):
        return {"reactor_name": self.reactor_name, "current_volume": self.current_volume, "current_mass": self.current_mass}
    
class Property(BaseModel):
    """
    A class defines the physical properties.
    Args:
        quantity: float type. the value of the physical property.
        unit: str type. the name of the unit of the physical property.
    """
    model_config = ConfigDict(extra="forbid")

    quantity: typing.Optional[float]
    unit: typing.Optional[str]
    
    @field_validator('quantity', mode='before')
    def validate_quantity(cls, value):
        # If the value is a string, check if it matches the required format
        if isinstance(value, str):
            if re.match(r"^___variable.*___$", value):
                warnings.warn("Defining a property using ___variable___. Make sure you are in template mode.")
                return value
            else:
                raise ValueError("quantity string must be in the format '___variable*___'")
        else:
            return value
        
    def __add__(self, other):
        if isinstance(other, Property) and (self.unit == other.unit):
            return Property(quantity = self.quantity + other.quantity, unit = self.unit)
        return NotImplemented
            
    def NL_rpt(self):
        """
        give the natural language representation of the physical property 
        """
        if self.quantity == None:
            quantity_txt = "<unknown quantity>"
        else:
            quantity_txt = str(self.quantity)
        
        if self.unit == None:
            unit_txt = "<unknown unit>"
        else:
            unit_txt = str(self.unit)

        return quantity_txt + " " + unit_txt
    
    def to_dict(self):
        return {
            "quantity": self.quantity,
            "unit": self.unit
        }
    
    def if_valid_unit(self):
        """
        Check if the current unit is valid for the current property name.
        e.g., g is not a valid unit for volume. 
        """
        pass 
        
class ChemicalNames(BaseModel):
    """
    A class defines the name of a compound.
    Args:
        chemical_id: python list type, List[str]. a list of strings of the molecular formula or the name of the compound. If not mentioned, uses empty list [].
        CAS_number: python list type, List[str]. a list of strings of the CAS number of the compound. If not mentioned, uses empty list [].
    """
    model_config = ConfigDict(extra="forbid")

    chemical_id: typing.Optional[typing.List[str]] 
    CAS_number: typing.Optional[typing.List[str]] = None 


class Liquid:
    """
    A class defines the identity of a liquid.
    Args:
        identity: a dict following the ChemicalNames format. it includes the possible names or CAS numbers of the liquid.
        concentration: a dict following the Property format. optional. it defines the concentration of a solution. if it is a pure liquid, concenration should be None.
        solvent: a dict defining an object from the "ChemicalNames" class. optional. it defines the solvent of the liquid. If the liquid is pure, solvent should be null. If the solvent is not mentioned, default to water.
    """

    def __init__(self,
                 identity: dict,
                 concentration: dict = None,
                 solvent: dict = None,
                 **kwargs):

        # initialize the concentration 
        _concentration = None 
        # define the identity of the chemicals
        if identity is not None:
            # if the concentration is inside the identity, record it 
            if "concentration" in list(identity.keys()):
                _concentration = identity.pop("concentration")
            self.identity = ChemicalNames(**identity)
        else:
            self.identity = ChemicalNames(chemical_id=None, CAS_number=None)
            
        # check if the concentration can be put 
        if concentration is not None:
            self.concentration = Property(**concentration) 
        # if the concentration is with the identity, put it 
        elif _concentration is not None:
            self.concentration = Property(**_concentration)
        # if the concentration is not defined anyway, define it as None
        else:
            self.concentration = Property(quantity=None, unit=None)
            
        if (concentration == None) and (_concentration == None):
            self.solvent = ChemicalNames(**solvent) if solvent is not None else ChemicalNames(chemical_id=None, CAS_number=None)
        else:
            self.solvent = ChemicalNames(**solvent) if solvent is not None else ChemicalNames(chemical_id=["H2O"], CAS_number=None)
        for k, v in kwargs.items():
            setattr(self, k, v)
        
        # exp required volume in mL
        self.exp_required_quantity = 0
        self.device = None

    def identity_text(self):
        return self.concat(self.identity.chemical_id, self.identity.CAS_number)
            
    def concat(self, l1, l2):
        if l1 is None and l2 is None:
            return []
        elif l1 is None:
            l1 = []
        elif l2 is None:
            l2 = []
        s = set(l1 + l2)
        return  list(s)


class Solid:
    """
    A class defines the identity of a solid.
    Args:
        identity: a dict following the ChemicalNames format. it includes the possible names or CAS numbers of the solid.
    """

    def __init__(self,
                 identity: dict,
                 **kwargs):
        self.identity = ChemicalNames(**identity) if identity is not None else ChemicalNames(chemical_id=None, CAS_number=None)
        for k, v in kwargs.items():
            setattr(self, k, v)
            
        # exp required mass in g
        self.exp_required_quantity = 0
        self.device = None
        
    def identity_text(self):
        return self.concat(self.identity.chemical_id, self.identity.CAS_number)
            
    def concat(self, l1, l2):
        if l1 is None and l2 is None:
            return []
        elif l1 is None:
            l1 = []
        elif l2 is None:
            l2 = []
        s = set(l1 + l2)
        return  list(s)   
