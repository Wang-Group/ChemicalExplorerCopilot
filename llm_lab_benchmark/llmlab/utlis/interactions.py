from typing import Union 
from llmlab.converter.llm_link.constants.units import UNITS, Property_unit_mapping
from llmlab.converter.llm_link.constants.chemicals import identical_names
from llmlab.constant import chemspider_api_key
from typing import Union
import pubchempy as pcp
from chemspipy import ChemSpider
from llmlab.utlis.property import Solid, Liquid, Property

cs = ChemSpider(chemspider_api_key)

# manually added identical names

def search_chemical_id(compound: Union[Solid, Liquid]):
    for chemical_id_index in range(len(compound.identity.chemical_id)):
        for identical_name in identical_names:
            if compound.identity.chemical_id[chemical_id_index] in identical_name:
                compound.identity.chemical_id.append(identical_name[0])
                compound.identity.chemical_id = list(dict.fromkeys(compound.identity.chemical_id[::-1]))
                return 
    return 
        
# search according to the CAS number or identity of the chemicals, return its common name and its molecular weight
def search_name_MW(compound: Union[Solid, Liquid]):
    """
    Get the actual name of the compound, and return it together with the molecular weight
    """
    # use the CAS number to search
    if compound.identity.CAS_number is not None:
        if len(compound.identity.CAS_number) > 0:
            while True:
                result = cs.search(compound.identity.CAS_number[0])
                if len(result) > 0:
                    return (result[0].common_name, result[0].molecular_formula), result[0].molecular_weight
                else:
                    input_temp = ask_for_cas(current_cas_num = compound.identity.CAS_number[0])
                    if input_temp == "skip":
                        break
                    else:
                        compound.identity.CAS_number[0] = input_temp

    # search accoridng to the name
    while True:
        # convert to standard again 
        search_chemical_id(compound = compound)
        # use the name of the chemical to search. 
        # search for the existing database, if this succeed, we will definitely find the information of chemicals 
        result = pcp.get_compounds(compound.identity.chemical_id[0], "name")
        if len(result) > 0:
            return (result[0].synonyms[0], result[0].molecular_formula), result[0].molecular_weight
        else:
            input_temp = ask_for_chemical_names(current_chemcial_name = compound.identity.chemical_id[0])
            if input_temp == "skip":
                return None, None
            else:
                compound.identity.chemical_id[0] = input_temp

# search according to the names
def search_name(compound: Union[Solid, Liquid]):
    """
    Get the actual name of the compound
    """
    # use the name of the chemical to search, if the above failed
    for chemical_id_index in range(len(compound.identity.chemical_id)):
        for identical_name in identical_names:
            if compound.identity.chemical_id[chemical_id_index] in identical_name:
                compound.identity.chemical_id.append(identical_name[0])
        compound.identity.chemical_id = list(dict.fromkeys(compound.identity.chemical_id[::-1]))

def standardize_unit(step, key_temp: str, value_temp: Property, property_type: str, raise_error_directly = False):
    """
    convert the unit of a value_temp (a property). if the unit is not listed in UNITS, ask the user to correct the current unit. 
    Args:
        step: an execution step where the unit should be checked.
        key_temp: the name of the property. 
        value_temp: the property object contaning the value and unit. 
    Returns:
        if the use has added new information to the platform 
    """
    # if it is not a property, do nothing
    if not (isinstance(value_temp, Property)):
        return
    # if it got no unit and quantity, do nothing
    if (value_temp.quantity is None) and (value_temp.unit is None):
        return
    # else, begin to check 
    else:
        print(100*"#", flush = True)
        if step is not None:
            print(f"""Function: {step.__class__.__name__} \nProperty: {key_temp} """, flush = True)
        else:
            print(f"""{key_temp}""", flush = True)
        print("before conversion:", flush = True)
        print(property_type, value_temp.quantity, value_temp.unit, flush = True)
        
        while True:
            supported_units = Property_unit_mapping[property_type]
            # if the unit is insidie the list, complete the transform and return 0
            for unit_name in supported_units:
                unit_type = UNITS[unit_name]
                if value_temp.unit in unit_type.keys():
                    value_temp.quantity = (value_temp.quantity / unit_type[value_temp.unit][0] +
                                            unit_type[value_temp.unit][1]) * unit_type[unit_type["target"]][0] - \
                                            unit_type[unit_type["target"]][1]
                    value_temp.unit = unit_type["target"]
                    print("after conversion:", flush = True)
                    print(value_temp.quantity, value_temp.unit, flush = True)
                    return
            
            if raise_error_directly:
                # raise error directly if unit is not supported. 
                raise ValueError(f"""the unit <{value_temp.unit}> is not supported for property <{property_type}>!""")
            else:
                # if the unit does not exist, ask the user about it 
                unit = ask_for_unit(value_temp)
                if unit == "skip":
                    print("interpreting the current unit with the platform default unit", flush = True)
                    return
                else:
                    value_temp.unit = unit
                
def convert_empty_substance_info(substance: Union[Liquid, Solid]):
    """
    convert the None to [], which will be used for sets later.
    """
    # convert None type to empty list, in case there random error occues when using set 
    if substance.identity.chemical_id == None:
        substance.identity.chemical_id = []
    if substance.identity.CAS_number == None:
        substance.identity.CAS_number = []
    if isinstance(substance, Liquid):
        if substance.solvent.chemical_id == None:
            substance.solvent.chemical_id = []
        if substance.solvent.CAS_number == None:
            substance.solvent.CAS_number = []
            
def convert_name(value_temp: Union[Liquid, Solid]):
    
    if (value_temp.identity.chemical_id is not None) or (value_temp.identity.CAS_number is not None):
        print("before conversion:", flush = True)
        print(value_temp.identity.chemical_id, flush = True)

        molecule, MW = search_name_MW(value_temp)
        # record the chemical formula and molecular weight 
        value_temp.formula = molecule 
        value_temp.MW = float(MW)
        
        print("after conversion:", flush = True)
        print(value_temp.identity.chemical_id, flush = True)

    convert_empty_substance_info(value_temp)
        
                
def ask_for_unit(value_temp: Property, mode = "plain_txt"):
    """
    Ask the usr for a unit
    """
    if mode == "plain_txt":
        print(f"""Warning: the current unit does not exist in the database.""", flush = True)
        print(f"""please offer a new and valid unit or enter "skip" to skip!""", flush = True)
        unit = input()
        
    elif mode =="llm_audio":
        pass 
    
    elif mode =="llm_txt":
        pass 
        
    return unit

def ask_for_physical_property(property_name, property_value, mode = "plain_txt"):
    """
    Ask the user for a Property type item to get rid of any ambiguity 
    """
    if mode == "plain_txt":
        print(f"""Warning: there is ambiguity in the definition of {property_name}.""", flush = True)
        print(f"""Its current value is <{property_value}>.""", flush = True)
        print(f"""please input a valid value to get rid of the ambiguity.""", flush = True)
        print(f"""Use -u if the input has a unit, -f if the string is a number, or -s if the input is a string.""", flush = True)

        input_info = str(input()).split()
        if input_info[0] == "-u":
            to_return = Property(quantity = float(input_info[1]), unit = str(input_info[2]))
            return to_return
        elif input_info[0] =="-s":
            to_return = str(" ".join(input_info[1:]))
            return to_return 
        elif input_info[0] =="-f":
            to_return = float(input_info[1])
            return to_return
        else:
            raise ValueError("the prefix must be -u, -s or -f")
    

def ask_for_cas(current_cas_num: str, mode = "plain_txt"):
    """
    Ask the user for a new CAS number 
    """
    if mode == "plain_txt":
        print(f"""Warning: cas number {current_cas_num} does not exist in the database.""", flush = True)
        print(f"""please offer a new CAS number or enter "skip" to skip!""", flush = True)
        cas_num = input()
        
    elif mode =="llm_audio":
        pass 
    
    elif mode =="llm_txt":
        pass 
    
    return cas_num

def ask_for_chemical_names(current_chemcial_name: str, mode = "plain_txt"):
    """
    Ask the user to give a chemical_name
    """
    if mode == "plain_txt":
        print(f"""warning: chemical name {current_chemcial_name} does not exist in the database""", flush = True)
        print(f"""please offer a new chemical name or enter "skip" to skip!""", flush = True)
        print("""If enter 'skip', no molecular weight for this compound will be found.""", flush = True)
        chemical_name = input()
        
    elif mode =="llm_audio":
        pass 
    elif mode =="llm_txt":
        pass 
    
    return chemical_name