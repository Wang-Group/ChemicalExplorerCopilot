import re
import os
import json
from datetime import datetime
from llmlab.llm.prompt_test import semantic_prompt
from llmlab.utlis.gpt import find_corresponding_text
import time 

def save_to_json(data, working_path):
    # generate unique file name
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    filename = f"output_{timestamp}.json"

    # generate file path
    file_path = os.path.join(working_path + "/", filename)
    os.makedirs(working_path+"/", exist_ok = True)
    # write output into json file
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    return file_path


def write_json(json_dict, json_path):
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(json_dict, json_file, ensure_ascii=False, indent=4)
        
def write_jsonl(data, path):
    # Write the list to a JSONL file
    with open(path, 'w') as file:
        for item in data:
            json_line = json.dumps(item)
            file.write(json_line + '\n')


def semantic_check(function_info, NL, model, function_set):
    for function in function_info:
        function_name = function["function_name"]
        function_args = function["function_args"]
        function_args_new = json.dumps(function_args, indent=2)

        matching_to_send = semantic_prompt.format(
            function_name=function_name,
            function_args=function_args_new,
            function_set=function_set,
            NL=NL,
        )
        result = find_corresponding_text(matching_to_send, model=model)
        # print(f"Result for function {function_name}:\n{result}\n")  # Debugging output

        # Extract the segment from the result
        match = re.search(
            r'(?:"([^"]+)"|The function arguments provided are:\n\n[^-]+-\s+\*[^*]+\*\s+([^"]+)\.")',
            result,
        )
        if match:
            sentence = match.group(1) if match.group(1) else match.group(2)
        else:
            sentence = "Segment not found"

        # Check for consistency
        is_consistent = (sentence != "Segment not found")

        function["original_content_of_steps"] = sentence
        function["is_consistent"] = is_consistent

    semantic_errors_list = []
    for func in function_info:
        if not func.get("is_consistent", True):
            semantic_errors = {
                "is_consistent": False,
                "semantic_errors": {
                    "message": "The content in 'original_content_of_steps' does not match the 'function_name' and 'function_args'.",
                    "original_content_of_steps": func.get(
                        "original_content_of_steps", ""
                    ),
                    "function_name": func.get("function_name", ""),
                    "function_args": func.get("function_args", {}),
                },
            }
            semantic_errors_list.append(semantic_errors)
            
    if semantic_errors_list:
        raise ValueError(f"Some error occured. The error is {semantic_errors_list}")
