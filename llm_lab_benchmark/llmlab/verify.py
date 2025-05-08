import json
import llmlab
import inspect
import llmlab.operations.exp_operation


"""
verify mandatory properties and optional proprties.

"""

functions = {
    "AddLiquid": llmlab.operations.exp_operation.AddLiquid,
    "AddSolid": llmlab.operations.exp_operation.AddSolid,
    "AdjustpH": llmlab.operations.exp_operation.AdjustpH,
    "AdjustTemperatureTo": llmlab.operations.exp_operation.AdjustTemperatureTo,
    "AdjustTemperatureForDuration": llmlab.operations.exp_operation.AdjustTemperatureForDuration,
    "Filter": llmlab.operations.exp_operation.Filter,
    "StirForDuration": llmlab.operations.exp_operation.StirForDuration,
    "StartStir": llmlab.operations.exp_operation.StartStir,
    "StopStir": llmlab.operations.exp_operation.StopStir,
    "TransferLiquid": llmlab.operations.exp_operation.TransferLiquid,
    "TransferSolid": llmlab.operations.exp_operation.TransferSolid,
    "Wait": llmlab.operations.exp_operation.Wait,
    "Recrystallization": llmlab.operations.exp_operation.Recrystallization,
    "Centrifuge": llmlab.operations.exp_operation.Centrifuge,
    "WashSolid": llmlab.operations.exp_operation.WashSolid,
    "Dry": llmlab.operations.exp_operation.Dry,
    "Precipitate": llmlab.operations.exp_operation.Precipitate,
    "Evaporate": llmlab.operations.exp_operation.Evaporate,
    "Yield": llmlab.operations.exp_operation.Yield
}

# generate mandatory/optional properties according to functions rather than set them manually 
mandatory_properties = {}
optional_properties = {}

for i in functions.keys():
    signature = inspect.signature(functions[i].__init__)
    mandatory_args = [param.name for param in signature.parameters.values() if param.default == param.empty]
    optional_args = [param.name for param in signature.parameters.values() if param.default != param.empty]
    # drop self
    try:
        mandatory_args.remove("self")
        optional_args.remove("self")
    except:
        pass
    
    mandatory_properties[i] = mandatory_args
    optional_properties[i] = optional_args
    # print(i, mandatory_properties[i])
    # print(i, optional_properties[i])
# solid_properties = ["identity", "purity"]
# liquid_properties = ["identify", "concentration", "solvent"]

def validate_properties(data):
    errors = []

    for function in data["function"]:
        function_name = function["function_name"]
        function_args = function["function_args"]
        
        if function_name not in mandatory_properties:
            errors.append(f"Unknown function_name: {function_name}")
            continue
        
        mandatory_args = mandatory_properties[function_name]
        optional_args = optional_properties[function_name]

        # Check mandatory properties
        for prop in mandatory_args:
            if prop not in function_args or function_args[prop] is None:
                errors.append(f"Missing or None value for mandatory property '{prop}' in function '{function_name}'")

        # Check optional args
        for arg in function_args:
            if arg not in mandatory_args and arg not in optional_args:
                errors.append(f"Unknown optional argument '{arg}' in function '{function_name}'")

    return errors


# def verify_synthesis(data, available_reactor, available_solid, available_liquid):
#     error_list = []
#     # # verify reactor available
#     # if "reactor" not in data or data["reactor"]["name"] not in available_hardware:
#     #     error_list.append({"step": "Reactor verification", "errors": ["Reactor hardware is not available"]})

#     # # verify solid and liquid available
#     # for reagent_type in ["solid", "liquid"]:
#     #     if reagent_type in data:
#     #         for reagent_name, reagent_details in data[reagent_type].items():
#     #             if reagent_name not in available_reagents:
#     #                 error_list.append({"step": f"{reagent_type} verification",
#     #                                    "errors": [f"Reagent {reagent_name} is not available"]})

#     # verify function name and args available
#     for function in data.get("function", []):
#         for action, params in function.items():
#             # verify mandatory properties
#             if action in mandatory_properties:
#                 missing_mandatory_props = [prop for prop in mandatory_properties[action] if prop not in params]
#                 if missing_mandatory_props:
#                     error_list.append(
#                         {"action": action, "errors": [f"Missing mandatory properties: {missing_mandatory_props}"]})
#             else:
#                 error_list.append(
#                     {"action": action, "errors": ["Action is not defined in the mandatory properties list."]})

#             # verify optional properties
#             unknown_optional_props = [prop for prop in params if
#                                       prop not in optional_properties.get(action, []) + mandatory_properties.get(action,
#                                                                                                                  [])]
#             if unknown_optional_props:
#                 error_list.append(
#                     {"action": action, "errors": [f"Unknown optional properties: {unknown_optional_props}"]})
                
#             # Get the corresponding class from the function map
#             function_class = functions.get(action)
    
#             if function_class:
#                 # Create an instance of the class
#                 instance = function_class(**params)
#                 # Call the translate_NL method
#                 result = instance.translate_NL()
#                 print(result)

#     return error_list









# def verify_json(response, available_reactor=None, available_solid=None, available_liquid=None):
#     """
#     Verify JSON and return errors
#     :param json_str: The JSON string to verify
#     :return: Returns an empty list if the input is valid.
#              Returns a string if the input cannot be parsed as JSON.
#              Returns a list of dictionaries if it has errors. Each element has two fields.
#                "step": The string of the line which contains error.
#                "errors": The error messages for that line.
#     """
#     try:
#         # parse JSON
#         data = json.loads(response)
#     except json.JSONDecodeError as e:
#         return "Input JSON cannot be parsed, there is a JSONDecodeError: {}".format(str(e))

#     # # Using json.dumps to pretty print the dictionary
#     # print(json.dumps(data, indent=4))
#     return verify_synthesis(data, available_reactor, available_solid, available_liquid)