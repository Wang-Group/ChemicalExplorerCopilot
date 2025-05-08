from llmlab.utlis.property import Property, Liquid, Solid
import inspect
from copy import copy
from llmlab.utlis.interactions import standardize_unit
from typing import Union

def ask_for_dilution(liquid: Liquid, mode = "plain_txt"):
    """
    Ask the user to add new solution or skip the current preparation from dilution
    """
    if mode == "plain_txt":
        print(100*"#", flush = True)
        print(f"""current liquid can not be prepared from dilution.""", flush = True)
        print("""enter "skip" to skip, or type anything for other options""", flush = True)
        id_string = inspect.cleandoc(f"""
        Common names: {liquid.identity.chemical_id + liquid.identity.CAS_number}
        Solvent: {liquid.solvent}
        Concentration: {liquid.concentration.NL_rpt()}""")
        
        print(id_string, flush = True)
        
        liquid_info = input()
        # if it is skip, do nothing
        if liquid_info == "skip":
            return liquid_info, None
        else:
            # double check the concentration of the liquid 
            if liquid.concentration == Property(quantity = None, unit = None):
                print(f"""the concentration of the current liquid is None, indicating it is a pure liquid but does not exist in the platform.""", flush = True)
                print(f"""enter y/Y/yes to confirm it, or enter its real concentration, e.g., 10 mol/L.""", flush = True)
                input_info = str(input())
                if (input_info == "yes") or (input_info == "y") or (input_info =="Y"):
                    pass
                else:
                    liquid.concentration.quantity = float(input_info.split()[0])
                    liquid.concentration.unit = input_info.split()[1]
                    standardize_unit(None, liquid.identity_text(), liquid.concentration, property_type = "concentration")
                    return None, None
                
            # copy the liquid 
            new_liquid = copy(liquid)
            # if it is a pure liquid, no concentration is considered and the user do not need to offer it 
            if liquid.concentration == Property(quantity = None, unit = None):
                print(f"""enter anything after adding the pure liquid to the platform!""", flush = True)
                input_info = str(input())
                return liquid_info, new_liquid
            else:
            # if it is a solution, ask the user to offer the concentration as a json dict. 
                print(f"""enter the concentration of the new solution added to the platform, e.g., 10 mol/L""", flush = True)
                input_info = str(input()).split()
                concentration = {"quantity": float(input_info[0]), "unit": input_info[1]}
                # convert the json 
                concentration = Property(**concentration)
                # assign the concentration to the new liquid, standarize and return it 
                new_liquid.concentration = concentration
                standardize_unit(None, new_liquid.identity_text(), new_liquid.concentration, property_type = "concentration")

                return liquid_info, new_liquid
            
    elif mode =="llm_audio":
        pass 
    elif mode =="llm_txt":
        pass 
    
    return liquid_info, new_liquid

def ask_for_dissolve(liquid: Liquid, mode = "plain_txt"):
    """
    Ask the user to add solid to the system when one solution needs to be prepared from dissolving. 
    """
    if mode == "plain_txt":
        print(100*"#", flush = True)
        print(f"""current liquid can not be prepared from dissolving a solid.""", flush = True)
        print(f"""enter "skip" to skip or type anything and offer the desired solid to the system!""", flush = True)
        
        id_string = inspect.cleandoc(f"""
        Common names: {liquid.identity.chemical_id + liquid.identity.CAS_number}
        Solvent: {liquid.solvent}
        Concentration: {liquid.concentration.NL_rpt()}""")
        
        print(id_string, flush = True)
        
        liquid_info = input()
        # if skip, do nothing 
        if liquid_info == "skip":
            return liquid_info, None
        else:
            # else, copy the identity information of the liquid and assign it to a solid. return the new solid. 
            print(f"""enter yes/y/Y if the solid ({liquid.identity.chemical_id[0]}) has been offered""", flush = True)
            input_info = input()
            if (input_info == "yes") or (input_info == "y") or (input_info =="Y"):
                new_solid = Solid(identity = dict(liquid.identity))
                return liquid_info, new_solid
            else:
                raise ValueError("please enter yes/y/Y after the compound is offered.")

    elif mode =="llm_audio":
        pass 
    elif mode =="llm_txt":
        pass 
    
def ask_for_solid(solid: Solid, mode = "plain_txt"):
    """
    Ask the user to add solid to the system when a solid should be used 
    """
    if mode == "plain_txt":
        print(100*"#", flush = True)
        print(f"""current solid does not exist in the platform.""", flush = True)
        print(f"""enter "skip" to skip or type anything and offer the desired solid to the system!""", flush = True)
        print(f"""Common names: {solid.identity.chemical_id + solid.identity.CAS_number}""", flush = True)  
              
        _info = input()
        # if not adding, do nothing (sanity check will get the user back to this point later)
        if _info == "skip":
            return _info, None
        else:
            # else, copy the identity information of the solid and assign it to a solid. return the new solid. 
            print(f"""enter yes/y/Y if the solid ({solid.identity.chemical_id[0]}) has been offered""", flush = True)
            input_info = input()
            if (input_info == "yes") or (input_info == "y") or (input_info =="Y"):
                new_solid = Solid(identity = dict(solid.identity))
                return _info, new_solid
            else:
                raise ValueError("please enter yes/y/Y after the compound is offered.")

    elif mode =="llm_audio":
        pass 
    elif mode =="llm_txt":
        pass 

def ask_for_device_info(compound: Union[Solid, Liquid], mode = "plain_txt"):
    """
    Ask the user about the hardware connection information of the added compound
    """
    # make sure the compoudn type is correct. 
    if not (isinstance(compound, Solid) or isinstance(compound, Liquid)):
        raise ValueError(f"""unsupported compound type!""") 
    
    if mode == "plain_txt":
        print(f"""enter a valid device connection for the added compound ({compound.identity.chemical_id[0]})""", flush = True)
        print(f"""It can be a string of the connection of the devices, e.g., "pump storage_liquid1" for liquid, or "4-OH-TEMPO_trace 5" for solid.""", flush = True)
        print(f"""The default mass of head will be set as 5 g if not clarified.""", flush = True)

        input_info = str(input()).split()
        
        # if it is a liquid, append the pump information to the device
        if isinstance(compound, Liquid):
            compound.device = {input_info[0]: input_info[1]}
        # if it is a solid, append to the solid header to the device 
        elif isinstance(compound, Solid):
            if len(input_info) ==1:
                input_info.append(5)
                
            compound.device = {
                "head": input_info[0],
                "maximum_mass (g)": float(input_info[1])
                }
        
    elif mode =="llm_audio":
        pass 
    elif mode =="llm_txt":
        pass 