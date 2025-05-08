import json
from logging import Logger
import llmlab 
from typing import Union
from llmlab.converter.llm_link.constants.units import UNITS
from llmlab.converter.llm_link.constants.supported_functions import SUPPORTED_FUNCTIONS
from llmlab.utlis.logic_interactions import ask_for_dilution, ask_for_dissolve, ask_for_solid, ask_for_device_info
from llmlab.utlis.interactions import standardize_unit, convert_empty_substance_info, convert_name
from llmlab.utlis.property import get_min_max_values
from llmlab.sanity_check.simulation.simulation import simulate_exp
import numpy as np 
from llmlab.sanity_check.syntax.response_to_function import parse_response_to_functions_exp
from llmlab.utlis.property import get_dict_from_object, replace_empty_arrays
from copy import copy 

class NLManager():

    def __init__(self, materials_path: str, json_path: str, logger: Logger):
                
        # initialize exp related things 
        self.logger = logger
        self.UNITS = UNITS
        self.load_materials(materials_path)
        
        self.json_path = json_path
        with open(self.json_path, encoding = "utf-8") as json_data:
            self.json_data = json.load(json_data)
            
        # parse and get the function set
        self.parse_function_set()
        self.get_function_set()
        
    def load_materials(self, materials_path):
        # read in the materials 
        with open(materials_path, "r", encoding = "utf-8") as f:
            self.materials = json.load(f)

        # append the storage liquid
        self.storage_liquid = []
        for liquid in self.materials["Liquid"]:
            for key_temp, value_temp in liquid.items():
                a = llmlab.utlis.property.Liquid(
                    **({"identity": {"chemical_id": [key_temp], "CAS_number": [key_temp]}}))
                a.device += value_temp["connection"]
                self.storage_liquid.append(a)
        for liquid in self.storage_liquid:
            convert_empty_substance_info(liquid)

        # append the storage solid
        self.storage_solid = []
        for solid in self.materials["Solid"]:
            for key_temp, value_temp in solid.items():
                a = llmlab.utlis.property.Solid(
                    **{"identity": {"chemical_id": [key_temp], "CAS_number": [key_temp]}})
                a.device.append(value_temp)
                self.storage_solid.append(a)
        for solid in self.storage_solid:
            convert_empty_substance_info(solid)
            
    def parse_function_set(self):
        """
        Perform sanity check from the data and read their properties
        Args:
            data: a processed json object from llmlab
        """
        # parse the function
        self.parsed_functions, self.errors = parse_response_to_functions_exp(self.json_data["function"])
        
    def get_function_set(self):
        """
        Express the parsed functions in json format
        """
        # get the function set from the parsed_functions
        self.func_set = []
        
        # need to rewrite it to recover the json file 
        for i in self.parsed_functions:
            func_name = i.__class__.__name__
            mad_args = llmlab.verify.mandatory_properties[func_name]
            opt_args = llmlab.verify.optional_properties[func_name]
            args = mad_args + opt_args
            dict_temp = {}
            for arg_name in args:
                dict_temp[arg_name] = getattr(i, arg_name)
            self.func_set.append({func_name: dict_temp})
            
    def acquire_current_parsed_functions(self):
        """
        Return the current parsed functions. 
        """
        to_export = []
        for func in self.parsed_functions:
            to_export.append(
                {"function_name": func.__class__.__name__, "function_args": get_dict_from_object(func)}
            )
        return to_export
        
    def export_current_function_to_json(self, out_path = "./out.json"):
        """
        Export the current parsed_funcs to a json file. 
        """
        to_export = []
        for func in self.parsed_functions:
            to_export.append(
                {"function_name": func.__class__.__name__, "function_args": get_dict_from_object(func)}
            )
        data_out = copy(self.json_data)
        data_out["function"] = to_export

        with open(out_path, "w") as json_data:
            json.dump(replace_empty_arrays(data_out), json_data, ensure_ascii=False, indent = 4)
                    
    def convert_property_to_standard_unit(self, raise_error_directly = False):
        """
        Convert all the units in the properties to the desired unit (i.e., the unit of the "target")
        """
        # check the properties of individual functions 
        for i in self.func_set:
            for key_temp, value_temp in list(i.values())[0].items():
                # if it is a property type, convert it directly
                if (isinstance(value_temp, llmlab.utlis.property.Property)):
                    standardize_unit(self.parsed_functions[self.func_set.index(i)], key_temp, value_temp, property_type = key_temp, raise_error_directly = raise_error_directly)
                    
                # if it is a Liquid, get the concentration respectively 
                elif isinstance(value_temp, llmlab.utlis.property.Liquid):
                    liquid_identity = value_temp.identity_text()
                    key_temp = "concentration"
                    value_temp = value_temp.concentration
                   
                    # check if it is a property type or not, if so, convert it directly
                    if (isinstance(value_temp, llmlab.utlis.property.Property)):
                        standardize_unit(None, liquid_identity, value_temp, property_type = key_temp, raise_error_directly = raise_error_directly)
                    # if it is a dict, it may contain min/max values
                    elif isinstance(value_temp, dict):
                        results = get_min_max_values(value_temp)
                        # convert the min/max values respectively if they are property type
                        for result_temp in results:
                            standardize_unit(None, liquid_identity, result_temp, property_type = key_temp, raise_error_directly = raise_error_directly)
                            
                # if it is a dict, check if min/max are keys of it.
                elif isinstance(value_temp, dict):
                    results = get_min_max_values(value_temp)
                    # convert the min/max values respectively if they are property type
                    for result_temp in results:
                        standardize_unit(self.parsed_functions[self.func_set.index(i)], key_temp, result_temp, property_type = key_temp, raise_error_directly = raise_error_directly)
                    
        # check the concentration for each liquid 
        for liquid in self.storage_liquid:
            key_temp = "concentration"
            value_temp = liquid.concentration
            if (isinstance(value_temp, llmlab.utlis.property.Property)):
                standardize_unit(None, liquid.identity_text(), value_temp, property_type = key_temp, raise_error_directly = raise_error_directly)
            else:
                results = get_min_max_values(value_temp)
                for result_temp in results:
                    standardize_unit(None, liquid.identity_text(), result_temp, property_type = key_temp, raise_error_directly = raise_error_directly)

    def convert_chemical_to_standard_names(self):
        for i in self.func_set:
            for key_temp, value_temp in list(i.values())[0].items():
                if isinstance(value_temp, llmlab.utlis.property.Liquid) or isinstance(value_temp, llmlab.utlis.property.Solid):
                    convert_name(value_temp = value_temp)
        
    def extract_solid(self):
        """
        Read the solid that involved in the whole process
        """
        # read in the solids that are used in the synthesis
        self.required_solid = []
        for i in self.func_set:
            for key_temp, value_temp in list(i.values())[0].items():
                if (isinstance(value_temp, llmlab.utlis.property.Solid)):
                    if len(value_temp.identity.CAS_number + value_temp.identity.chemical_id) != 0:
                        self.required_solid.append(value_temp)
                        
    def extract_liquid(self):
        """
        Read the liquid that will be used in the process
        """
        # read in the liquids that are used in the synthesis
        self.required_liquid = []
        for i in self.func_set:
            for key_temp, value_temp in list(i.values())[0].items():
                if (isinstance(value_temp, llmlab.utlis.property.Liquid)):
                    if len(value_temp.identity.CAS_number + value_temp.identity.chemical_id) != 0:
                        self.required_liquid.append(value_temp)
                        
    def extract_reactors(self):
        """
        Read the reactors that will be used in the process
        """
        self.required_reactors = []
        for i in self.func_set:
            for key_temp, value_temp in list(i.values())[0].items():
                if key_temp in ["reactor_name", "filtrate_vessel", "from_reactor", "to_reactor", "waste_vessel", "centrifuge_reactor"]:
                    self.required_reactors.append(value_temp)
        self.required_reactors = list(np.unique(self.required_reactors))
        
    def prepare_one_liquid_from_dilution(self, liquid: llmlab.utlis.property.Liquid):
        # all the names of the liquid
        set1 = liquid.identity.chemical_id + liquid.identity.CAS_number  # the liquid we will check and prepare
        set2 = [liquid_temp.identity.chemical_id + liquid_temp.identity.CAS_number for liquid_temp in
                self.storage_liquid]
        if len(set2) == 0:
            return False

        # if we have found the solution with the same chemical id
        for index in range(len(set2)):
            # find the liquid
            if bool(set(set1) & set(set2[index])):
                if (liquid.concentration.unit == self.storage_liquid[index].concentration.unit):
                    # check the unit, if they are the same, do nothing
                    if (liquid.concentration.quantity == self.storage_liquid[index].concentration.quantity):
                        return "Liquid", self.storage_liquid[index]
                    elif self.storage_liquid[index].concentration.quantity > liquid.concentration.quantity:
                        # we should prepare the solution by diluting
                        return "Dilute", self.storage_liquid[index]

        # if we did not find the liquid with the same concentration but we did find concentrated solution,
        # then we should consider diluting or prepare it from solid (function below)
        return False

    def prepare_one_compound_from_solid(self, compound: Union[llmlab.utlis.property.Liquid, llmlab.utlis.property.Solid]):
        # all the names of the solid
        set1 = compound.identity.chemical_id + compound.identity.CAS_number  # the solution we will check and prepare
        set2 = [solid_temp.identity.chemical_id + solid_temp.identity.CAS_number for solid_temp in self.storage_solid]
        if len(set2) == 0:
            return False
        for index in range(len(set2)):
            # find the solid
            if bool(set(set1) & set(set2[index])):
                return "Solid", self.storage_solid[index]
        return False
        
    def check_material_availability_nq(self):
        """
        Check if all the solids/liquids involved in the synthesis are available. non quantity check. 
        """
        # check the availability of getting solids from the weighing head 
        solid_prepare_procedure = []
        for solid_idx in range(len(self.required_solid)):
            solid = self.required_solid[solid_idx]
            while True:
                result_temp = (self.prepare_one_compound_from_solid(compound = solid))
                if result_temp != False:
                    solid_prepare_procedure.append(result_temp)
                    break
                else:
                    solid_info, new_solid = ask_for_solid(solid)
                    if solid_info == "skip":
                        solid_prepare_procedure.append(result_temp)
                        break
                    else:
                        ask_for_device_info(new_solid)
                        self.storage_solid.append(new_solid)
        
        # check the availability of getting solutions from dilution 
        liquid_prepare_procedure = []
        for liquid_idx in range(len(self.required_liquid)):
            liquid = self.required_liquid[liquid_idx]
            # iteratively interaction and check if the liquid can be prepared 
            while True:
                prepare_info = self.prepare_one_liquid_from_dilution(liquid = liquid)
                if prepare_info != False:
                    liquid_prepare_procedure.append(prepare_info)
                    break
                else:
                    # use GPT-4 to talk with human being to complete the information 
                    # fix me by prompting the human being 
                    liquid_info, new_liquid = ask_for_dilution(liquid)
                    if liquid_info == "skip":
                        liquid_prepare_procedure.append(prepare_info)
                        break 
                    # if the concentration of the liquid is changed, check it again in the next round
                    elif (liquid_info == None) and (new_liquid == None):
                        pass
                    # add the new liquid to the storage system
                    else:
                        # after adding the new liquid or change the concentration of the original liquid, normalize its unit
                        ask_for_device_info(new_liquid)
                        self.storage_liquid.append(new_liquid)
                        
        # check the availability of getting solutions from solids
        for liquid_idx in range(len(liquid_prepare_procedure)):
            liquid = self.required_liquid[liquid_idx]
            if liquid_prepare_procedure[liquid_idx] is False:
                while True:
                    result_temp = (self.prepare_one_compound_from_solid(compound = liquid))
                    if result_temp != False:
                        liquid_prepare_procedure[liquid_idx] = result_temp
                        break
                    else:
                        # use GPT-4 to talk with human being to complete the information 
                        # fix me by prompting the human being 
                        liquid_info, new_solid = ask_for_dissolve(liquid)
                        if liquid_info == "skip":
                            break
                        else:
                            # fix me by adding audio input etc.
                            # this can be modifying the required liquid, adding new things to the current mapping json, etc. 
                            ask_for_device_info(new_solid)
                            self.storage_solid.append(new_solid)
                            
        return solid_prepare_procedure, liquid_prepare_procedure
    
    def check_material_availability_q(self, ignore_quantity = True):
        pass 
    
    def check_function_ambiguity(self, verbose = True):
        """
        check if there is any ambiguity of the quantities
        """
        to_export = self.acquire_current_parsed_functions()
        
        # iterate through all the functions, check the type of each args, and see if there is any ambiguity and it can be executed. 
        count = 0 
        while True:
            error_num = 0 
            print(100*"*")
            print(f"""Ambiguity check trial {count}""", flush = True)
            for step_count in range(len(self.parsed_functions)):
                step = self.parsed_functions[step_count]
                print(100*"#", flush = True)
                print(json.dumps(to_export[step_count], indent = 4), flush = True)
                print(step.check_ambiguity())
                error_num = error_num + len(step.ambiguity_dict)
            if error_num ==0:
                break
            else:
                count = count + 1 
                
        # update the values in the function set
        self.get_function_set()

    def rescale_systems(self):
        # run a simulation, record the highest volume/ mass.
        # decide the scale factor according to the reactor_content 
        # rescale_factor_inverse is the maximum value of possible volume/maximum volume of the reactor 
        reactor_content, rescale_factor_inverse = simulate_exp(self.required_reactors, self.parsed_functions)
        
        # call each function to rescale it. 
        reagents_usage = []
        if rescale_factor_inverse > 1:
            rescale_factor = 1/rescale_factor_inverse
            print(f"rescaling the system: rescale_factor is {rescale_factor}")
        else:
            rescale_factor = 1
            
        # in this stage, the property of the functions should be explict values or property instead of string or dict with min/max values. 
        for step in self.parsed_functions:
            reagents_usage.append(step.rescale(rescale_factor = rescale_factor))
            
        return reagents_usage
    
    def get_consumption(self, reagents_usage, solid_prepare_procedure, liquid_prepare_procedure, tolerance = 0.2, abs_tolerance = 5, resolutin = 10):        
        """
        Estimate the consumption of Liquid and Solid in self.storage_liquid and self.storage_solid.
        Args:
            reagents_usage: the reagents_usage from self.rescale_systems, which contains the consumption of Solid/Liquid in self.required_solid/self.required_liquid.
            solid_prepare_procedure: solid_prepare_procedure from self.check_material_availability_nq, indicating how solid in self.required_solid is prepared. 
            liquid_prepare_procedure: liquid_prepare_procedure from self.check_material_availability_nq, indicating how liquid in self.required_liquid is prepared. 
            tolerance: the percentage tolerance for the usage of liquid in case the complete usage of the concentrated solution/liquid.
            abs_tolerance: the percentage tolerance for the usage of liquid. the higher value from tolerance or abs_tolerance will be used as the true tolerance. 
            resolutin: when we prepare solution from solids or dilution, we will prepare resolution mL, 2* resolution mL, etc..
        """
        # all the reagents are in either self.required_solid or self.required_liquid, or None (because no reagent was used in the specific step)
        # record how much of them are consumed
        for reagent in reagents_usage:
            if reagent != None:
                if not ((reagent[0] in self.required_solid) or (reagent[0] in self.required_liquid)):
                    raise ValueError(f"Error! One reagent({reagent[0]}) is missing in the required solid/liquid list.")
                else:
                    # accumulate the amount of reagent we should use 
                    reagent[0].exp_required_quantity = reagent[0].exp_required_quantity + reagent[1]

        # we know how each of the required_solid are prepared
        assert len(self.required_solid) == len(solid_prepare_procedure)
        # for the required_solid, we will check how they can be prepared, and add the required amount to their sources
        for index in range(len(self.required_solid)):
            solid_prepare_procedure[index][1].exp_required_quantity += self.required_solid[index].exp_required_quantity
            
        # we know how each of the required_liquid are prepared according to liquid_prepare_procedure
        assert len(self.required_liquid) == len(liquid_prepare_procedure)
        # for the required liquid, we should check how they are prepared and add the required amount to their either solid or liquid source 
        for index in range(len(self.required_liquid)):
            # if the source of the required liquid is a pure liquid, we just do a simple addition
            if liquid_prepare_procedure[index][0] == "Liquid":
                additional_q = self.required_liquid[index].exp_required_quantity 
                additional_q = additional_q + max(tolerance * additional_q, abs_tolerance) # with 20% more volume or abs_tolerance mL just in case
                liquid_prepare_procedure[index][1].exp_required_quantity += additional_q
                
            # if the source of the required liquid is a more concentrated liquid, we do it accoridng to the molar quantity
            elif liquid_prepare_procedure[index][0] == "Dilute":
                source_liquid = liquid_prepare_procedure[index][1]
                usage_liquid = self.required_liquid[index]
                usage_liquid.exp_required_quantity = np.ceil(usage_liquid.exp_required_quantity / resolutin) * resolutin # ceiling to resolutin mL
                additional_q = (usage_liquid.concentration.quantity * usage_liquid.exp_required_quantity / source_liquid.concentration.quantity)
                additional_q = additional_q + max(tolerance * additional_q, abs_tolerance) # with 20% more volume or 5 mL just in case
                source_liquid.exp_required_quantity += additional_q
                
            # if the source of the required liquid is a solid, we do it according to the molar concetrantion and the volume of the liquid
            elif liquid_prepare_procedure[index][0] == "Solid":
                source_solid = liquid_prepare_procedure[index][1]
                usage_liquid = self.required_liquid[index]
                # calcualte the actual amount of solid necessary to prepare the solutin with desired volume
                if usage_liquid.concentration.unit == "mol/L":
                    usage_liquid.exp_required_quantity = np.ceil(usage_liquid.exp_required_quantity / resolutin) * resolutin # ceiling to resolutin mL
                    additional_q =  usage_liquid.exp_required_quantity / 1000 * usage_liquid.concentration.quantity * float(usage_liquid.MW)
                elif usage_liquid.concentration.unit == "g/mL":
                    usage_liquid.exp_required_quantity = np.ceil(usage_liquid.exp_required_quantity / resolutin) * resolutin # ceiling to resolutin mL
                    additional_q = usage_liquid.exp_required_quantity * usage_liquid.concentration.quantity
                else:
                    raise ValueError("The unit of concentration must be either g/mL or mol/L")
                
                # add the additional quantity to the soruce solid 
                source_solid.exp_required_quantity += additional_q
                
            else:
                raise ValueError(f"""unsupported preparation type "{liquid_prepare_procedure[index][0]}". It must be "Solid", "Dilute", or "Liquid". """)
    
    def check_all_procedures(self):
        """
        Check the whole procedure to make sure there is not ambiguity and everything is standarized. 
        """
        # convert the names of the chemicals to their standard names 
        self.convert_chemical_to_standard_names()
        
        # convert the units of all the functions to their standard units 
        self.convert_property_to_standard_unit()
        
        # extract solid/liquid/reactors from the procedure 
        self.extract_solid()
        self.extract_liquid()
        self.extract_reactors()
        
        # get all the procedures that can be used to prepare solids/liquids 
        solid_prepare_procedure, liquid_prepare_procedure = self.check_material_availability_nq()
        
        # get rid of any ambiguity 
        self.check_function_ambiguity()
        
        # export the current functions before rescaling 
        self.export_current_function_to_json(out_path = self.json_path.replace(".json", "_temp.json"))
        
        # rescale the system and get the reagents that will be used 
        reagents_usage = self.rescale_systems()
        
        # get all the reagents that will be used
        self.get_consumption(reagents_usage, solid_prepare_procedure, liquid_prepare_procedure)
        
        # export the final json 
        self.export_current_function_to_json(out_path = self.json_path.replace(".json", "_temp_rescaled.json"))