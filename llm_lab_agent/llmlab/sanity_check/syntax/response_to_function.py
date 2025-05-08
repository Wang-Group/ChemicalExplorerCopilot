import ast
import json
from collections import OrderedDict
from llmlab.verify import functions as function_mapping


from pydantic import BaseModel

def convert_to_serializable(obj):
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif hasattr(obj, "to_dict"):
        return obj.to_dict()
    else:
        return obj

def parse_json(response):

    try:
        if isinstance(response, str):
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                data = ast.literal_eval(response)
        elif isinstance(response, dict):
            data = response
        else:
            # errors.append("Unsupported input type. Please provide a JSON string or a dictionary.")
            return None

    except json.JSONDecodeError as e:
        # errors.append("Input JSON cannot be parsed, there is a JSONDecodeError: {}".format(str(e)))
        return None
    
    return data

def response_to_list_exp(response):
    """
    Conver the response from the large language model to a python list
    args:
        response: the response from the LLM
    returns: 
        response_list: the list of the responses
    """
    try:
        if not isinstance(response, list):
            response_list = ast.literal_eval(response)
        else:
            response_list = response
        return response_list
    except:
        raise ValueError("fail to convert the response to a Python list. please respond with the required format, which can be converted to a Python list later.")

def parse_response_to_functions_exp(response):
    # conver the response to a python list first
    response_list = response_to_list_exp(response)
    # now, generate python functions
    functions = []
    errors = []
    for i in response_list:
        try:
            name = i["function_name"]
            args = i["function_args"]
        except:
            errors.append(f"Key error in {i}. It should have a key called 'function', with 'function_name' and 'function_args' as subkeys in it.")
            continue

        if name not in list(function_mapping.keys()):
            errors.append(f"Error when initializing the function from {i}! \n{name} is not a valid function name.")
            continue

        try:
            function = function_mapping[name](**args)
            functions.append(function)
        except Exception as e:
            error = str(e)
            errors.append(f"args error in {i}. {args} is not valid args for function {name}. the specific error is: {error}")
            continue 

    return functions, errors