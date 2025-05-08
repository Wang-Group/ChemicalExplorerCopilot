initial_prompt = """ \
You are an expert in robotic chemistry. According to the goal of the experiment and available functions, \
call a series of functions to perform experiments using the robot.

GOALS:
"{NL}"

The following described functions with their formatted args in the doulbe quotes can be called:
"{function_set}"

Rules:
1. Base your plan on the available functions.
2. Strictly obey the args for the individual functions. 

You should only respond in JSON format as described below and ensure the JSON object can be parsed by Python "json.loads", e.g., no trailing commas, no single quotes, etc.

Response Format: 
[
    {{
        "thoughts": {{
            "index": "1",
            "text": "<thought>",
            "reasoning": "<reasoning>",
            "plan": "<- short bulleted list that conveys long-term plan>",
            "criticism": "<constructive self-criticism>",
            "speak": "<thoughts summary to say to the user>"
            }},
        "function": {{
            "name": "<function name>", "args": {{"<arg name>": "<value>"}}
            }}
    }},

    {{
        "thoughts": {{
            "index": "2",
            "text": "<thought>",
            "reasoning": "<reasoning>",
            "plan": "<- short bulleted list that conveys long-term plan>",
            "criticism": "<constructive self-criticism>",
            "speak": "<thoughts summary to say to the user>"
            }},
        "function": {{
            "name": "<function name>", "args": {{"<arg name>": "<value>"}}
            }}
    }},
    ...
]
"""

iterative_prompt = """ \
Here is the response from the previous iteration in the double quote below:
"{json_object}"

This response is not correct or does not achieve the goal. Please correct the JSON object to achive the goals. The error of the JSON object is shown below in the double quote:
"{error}"

Please improve the JSON object and respond with the corrected JSON object.
"""

criticism_prompt = """ \
You are an assistant that assesses the following codes that control the robot. \
You are required to evaluate if the codes have met the task requirements. \
Exceeding the task requirements is also considered a success while failing to meet them requires you to provide critique to help me improve. \
I will give you the following information:

Code:
This is a Python list where each element corresponds to the name and the args of a function, \
and the functions in the list will be executed sequentially. \
The following described functions with their formatted args in the doulbe quotes can be called:
"{function_set}"

Task:
This is the description of the task in natural language format. 

You should only respond in JSON format as described below:
{{
"reasoning": "<reasoning>",
"success": <boolean, indicating if the task is achived or not>,
"critique": "<critique>"
}}
Ensure the response can be parsed by Python "json.loads", e.g., no trailing commas, no single quotes, etc.

Code:
"{code}"

Task:
"{NL}"

"""