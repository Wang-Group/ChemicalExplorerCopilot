import sys
sys.path.insert(0,r'')
import re
import os
import json
import pandas as pd
import pkg_resources
from datetime import datetime
from collections import OrderedDict
from llmlab.verify import validate_properties
from llmlab.converter.llm_link import NLManager
from llmlab.llm.prompt_test import initial_prompt, iter_prompt, semantic_prompt
from llmlab.utlis.gpt import get_completion, iter_completion, find_corresponding_text
from llmlab.sanity_check.syntax.response_to_function import parse_json

"""
Convert experimental procedures described in natural language into a formatted JSON file.
"""


function_set_path = pkg_resources.resource_filename('llmlab', '/llm/function_set.txt')
with open(function_set_path, "r", encoding='utf-8') as f:
    function_set = f.read()
    
reference_path = pkg_resources.resource_filename('llmlab', '/llm/reference_samples.txt')
with open(reference_path, "r", encoding='utf-8') as f:
    reference_samples = f.read()

Materials_Path = pkg_resources.resource_filename('llmlab', '/materials.json')

# model = "gpt-4-0125-preview"
# model = "gpt-4-turbo"
# model = "gpt-4o-2024-05-13"
model = "gpt-4o"

# Add a global counter for iter_convert calls
iter_convert_counter = 0

def save_to_json(data):
    # Prompt user for file path
    user_file_path = input("Please enter the file path to save the JSON file: ")

    # generate unique file name
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"output_{timestamp}.json"
    
    # generate file path
    file_path = os.path.join(user_file_path, filename)
    
    # write output into json file
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    
    return file_path

def write_json(json_dict, json_path):
    with open(json_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_dict, json_file, ensure_ascii=False, indent=4)   

def initial_convert(NL):    
    to_send = initial_prompt.format(function_set = function_set, reference_samples = None) # reference_samples = reference_samples

    try:
        gpt_response = get_completion(to_send, NL, model)
        # the output of GPT4 is ```json```
        start = gpt_response.find('json') + 4
        end = gpt_response.rfind('```')
        json_str = gpt_response[start:end].strip()

        try:
            # check and convert the response string to a dictionary
            json_dict = parse_json(json_str)
            Json_Path = save_to_json(json_dict)
            # print (Json_Path)
            # print (Json_Name)

            return check_function_args(NL, Json_Path)
        except Exception as e:
            print(f"Initial convert errors occured in checking and converting the response string to a dictionary: {e}")
            return None, None
        
    except Exception as e:
        print("Errors occured in response from initial convert: {e}")
        return None, None

def check_function_args(NL, Json_Path):
    json_mng = NLManager(materials_path = Materials_Path, json_path = Json_Path, logger = None)
    json_mng.parse_function_set() # parse_response_to_functions_exp

    if json_mng.errors:
        print("Errors occured in initial convert process! Next is iter convert!")
        function_info = json_mng.acquire_current_parsed_functions()
        errors_str = json.dumps(json_mng.errors)  # Convert errors list to JSON string
        return iter_convert(function_info, errors_str, NL, Json_Path)
    else:
        # function_info = json_mng.acquire_current_parsed_functions()
        return check_args_units(NL, json_mng, Json_Path)
    
def check_args_units(NL, json_mng, Json_Path):
    print (json_mng)
    print (type(json_mng))
    try:
        json_syntax_check = json_mng.convert_property_to_standard_unit(raise_error_directly=True)
        if not json_syntax_check:
            print("Syntax check process successful! Next is the syntax verification process for mandatory and optional arguments!")
            function_info = json_mng.acquire_current_parsed_functions()
            return syntax_verify(function_info, NL, Json_Path)
          
    except Exception as e:
        json_syntax_check_error = str(e)
        print(f"An error occurred during the syntax check process for converting property to standard units: {json_syntax_check_error}")
        function_info = json_mng.acquire_current_parsed_functions()
        errors_str = json.dumps([json_syntax_check_error])  # Convert the error message to JSON string 
        return iter_convert(function_info, errors_str, NL, Json_Path)                  

def iter_convert(function_info, errors, NL, Json_Path):
    global iter_convert_counter
    iter_convert_counter += 1

    if iter_convert_counter > 10:
        print("Maximum number of iter_convert calls reached. Stopping the iteration.")
        return None, Json_Path

    iter_to_send = iter_prompt.format(json_object = function_info, error = errors, function_set = function_set, reference_samples = None) # reference_samples = reference_samples

    try:
        iter_gpt_response = iter_completion(iter_to_send, NL, model)
        # print(iter_gpt_response)
        # the output of GPT4 is ```json```
        start = iter_gpt_response.find('json') + 4
        end = iter_gpt_response.rfind('```')
        json_str = iter_gpt_response[start:end].strip()
        # return json_str 

        try:
            # check and convert the response string to a dictionary
            json_dict = parse_json(json_str)
            write_json(json_dict, Json_Path)
            return check_function_args(NL, Json_Path)
        except Exception as e:
            print(f"Iter convert errors occurred in checking and converting the response string to a dictionary: {e}")
            return None, Json_Path
    
    except Exception as e:
        print(f"Errors occurred in response from iter convert: {e}")
        return None, Json_Path      

def syntax_verify(function_info, NL, Json_Path):  
    # Mandatory and optional properties checking
    prop_errors = validate_properties(function_info)

    if prop_errors:
        print("Errors occured in syntax verify process! Next is iter convert process!\n"
              f"errors are {prop_errors}")
        return iter_convert(function_info, prop_errors, NL, Json_Path)
    else:
        print("Success in syntax verify process! Next is semantic check process!")
        return semantic_check(function_info, NL, Json_Path)


def semantic_check(function_info, NL, Json_Path):
    for function in function_info:
        function_name = function["function_name"]
        function_args = function["function_args"]
        function_args_new = json.dumps(function_args, indent=2)

        matching_to_send = semantic_prompt.format(
                                            function_name = function_name, 
                                            function_args = function_args_new, 
                                            function_set = function_set, 
                                            NL = NL
                                            )        
        result = find_corresponding_text(matching_to_send, model = model)
        # print(f"Result for function {function_name}:\n{result}\n")  # Debugging output

        # Extract the segment from the result
        match = re.search(r'(?:"([^"]+)"|The function arguments provided are:\n\n[^-]+-\s+\*[^*]+\*\s+([^"]+)\.")', result)
        if match:
            sentence = match.group(1) if match.group(1) else match.group(2)
        else:
            sentence = "Segment not found"

        # Check for consistency
        is_consistent = sentence != "Segment not found"

        function["original_content_of_steps"] = sentence
        function["is_consistent"] = is_consistent

    semantic_errors_list = []
    for func in function_info:
        if not func.get('is_consistent', True):
            semantic_errors = {
                "is_consistent": False,
                "semantic_errors": {
                    "message": "The content in 'original_content_of_steps' does not match the 'function_name' and 'function_args'.",
                    "original_content_of_steps": func.get("original_content_of_steps", ""),
                    "function_name": func.get("function_name", ""),
                    "function_args": func.get("function_args", {})
                }
            }
            semantic_errors_list.append(semantic_errors)

    if semantic_errors_list:
        print("Errors occured in semantic check process! Next is iter convert process!")
        return iter_convert(function_info, semantic_errors_list, NL, Json_Path)
    else:
        # Insert new element
        new_element_key = "NL"
        new_element_value = NL

        # Create a new ordered dictionary and place the new element first
        new_format_json = OrderedDict([(new_element_key, new_element_value)])
        new_format_json["function"] = function_info
        print("All processes are successful!")
        return new_format_json, Json_Path
    

def main():
    NL = input("Please input an experimental procedure: ")

    # Convert NL to a formatted JSON file
    format_json, Json_Path = initial_convert(NL)
    if format_json and Json_Path:
        write_json(format_json, Json_Path) 
        print(f"The final json file is saved in {Json_Path}")
    else:
        print("Failed to convert the experimental procedure to JSON format.")


if __name__ == "__main__":
    main()