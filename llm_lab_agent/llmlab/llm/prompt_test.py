initial_prompt = """\
##############
ULE files follow JSON syntax and consist of two mandatory sections: "reactants" and "function". The section must be present and cannot be `null`.
1. **Reactants Section**: Describes the reactants involved in the experimental procedure, including solvent. The compounds that are synthesized during the process should not be included.
2. **Function Section**: Describes the synthetic actions involved in the experiment procedure, declared linearly. This section calls a series of functions to perform experiments using the robot.
3. **Function Set**: The function, with their formatted arguments, can be found below within the double quotes:
"{function_set}"
4. **Reference Samples**: Input-output examples where the input is a natural language description of experimental procedures and the output is a JSON file with functions describing those procedures, can be found below within the double quotes:
"{reference_samples}"
##############

##############
**Syntax Rules**:
1. **Read and Parse Input**: First, read all the input experimental procedures, then carefully parse all synthetic actions.
2. **Argument Selection Priority**: If an argument can be selected from Single value, Range, or Descriptive string, the priority is Single value > Range > Descriptive string. Use the default value of the arguments if the argument is not mentioned.
3. **Strictly Adhere to Function Arguments**: Strictly follow the arguments for each individual function, using the default value of the arguments if the argument is not mentioned.
4. **Generate Valid JSON**: Only respond with a ULE File in JSON format as described below and ensure the JSON object can be parsed by Python's `json.loads` (e.g., no trailing commas, no single quotes, etc.).
5. **Use Only Input Words**: Only use words that appear in the input experimental procedure. If the value of an argument is not mentioned in the input experimental procedure, you are forbidden to generate the value of the argument.
6. **Handle Non-standard Characters**: Normalize units to handle non-standard characters without changing the nature of the unit. For example, replace "mL−1" with "mg/mL" and ensure all minus signs are standard ASCII characters. Maintain the original units as they appear in the input, such as keeping "420μL" as "420μL" without converting to other units like "0.42mL".
##############

##############
**Experimental Operation Knowledge**:
1. **Perform One Action at a Time**: Perform one action at a time on only one reagent or reactor. For example, if the raw text is "wash with A and B," the order is washing with A and then washing with B.
2. **Order of Chemical Reactions**: The order of operations is crucial. For example, if the raw text is "adding A to a solution of B and C in D (i.e. solvent)," the order is adding solvent D to reactor 1, adding reagent B to reactor 1, adding reagent C to reactor 1, and then adding A to reactor 1. Another example is when the text is "A was added to B (e.g., solvent or an existing solution)", B should be added to the reactor first, then A should be added or transferred to the same reactor. This is common when adding a solution to a solvent (e.g., water) to dilute it. 
3. **Complete Purification Process**: The full purification process with the precipitation method refers to three steps in sequence: precipitate, filtration, and wash solid. If the repeat times of the purification process are twice, you should call in sequence: precipitate, filtration, wash solid, precipitate, filtration, wash solid, but not precipitate, precipitate, filtration, filtration, wash solid, wash solid. In each function, the repeat times is 1.
4. **Concentration Representation**: The capital M represents concentration, which is equal to mol/L.
5. **Reuse of the Compounds Synthesized in the Procedure**: The procedure can involve the synthesis of several compounds. The synthesized compounds can be used within the same procedure. In this case, determine which reactors the compounds are, and use TransferLiquid or TransferSolid to use them. This is very common in seed-mediated synthesis. One example is when the seed solution is previously synthesized, TransferLiquid should be used to add the seed solution to the growth solution. Do not use AddLiquid in this process. Another example is when the raw text is "The turbid liquid was sealed in a 23 ml Teflon lined autoclave," determine which container the turbid liquid was in during the previous step. If it is not already in the Teflon lined autoclave, you need to call the function "TransferLiquid" to transfer the turbid liquid from the original container to the Teflon lined autoclave.
6. **Stirring and Heating**: When the operation "stir" or "agitate" occurs with other operations, like "agitate and heat," you should call the function "AdjustTemperatureTo" or "AdjustTemperatureFor" according to the description, but not call the function "StirForDuration."
7. **Stock Solution**: If there are any stock solutions mentioned in the context, treat them as existing compounds that have already been prepared by us, without the need for special preparation.
##############

##############
ULE File Format:
{{  "reactants": [
    {{
        "reactant": "<name of the reactant>"
    }},
    {{
        "reactant": "<name of the reactant>"
    }},
    ...
    ],
    "function":[
    {{
        "function_name": "<function name>",
        "function_args":{{
            "<arg name>": "<value>",
            "<arg name>": "<value>"
            ...
            }}
        ...
    }},
    {{
        "function_name": "<function name>",
        "function_args":{{
            "<arg name>": "<value>",
            "<arg name>": "<value>"
            ...
            }}
        ...
    }}
    ...
    ]
}}
##############

"""

iter_prompt = """ \
Here is the response from the previous iteration in the double quotes below: "{json_object}".
This response is not correct or does not achieve the goal. You should parse the input experimental procedures again and output ULE files. \
The error in the JSON object is shown below in the double quotes: "{error}". This time, you should correct the errors. \

##############
ULE files follow JSON syntax and consist of two mandatory sections: "reactants" and "function". The section must be present and cannot be `null`.
1. **Reactants Section**: Describes the reactants involved in the experimental procedure, including solvent. The compounds that are synthesized during the process should not be included.
2. **Function Section**: Describes the synthetic actions involved in the experiment procedure, declared linearly. This section calls a series of functions to perform experiments using the robot.
3. **Function Set**: The function, with their formatted arguments, can be found below within the double quotes:
"{function_set}"
4. **Reference Samples**: Input-output examples where the input is a natural language description of experimental procedures and the output is a JSON file with functions describing those procedures, can be found below within the double quotes:
"{reference_samples}"
##############

**Syntax Rules**:
1. **Read and Parse Input**: First, read all the input experimental procedures, then carefully parse all synthetic actions.
2. **Argument Selection Priority**: If an argument can be selected from Single value, Range, or Descriptive string, the priority is Single value > Range > Descriptive string. Use the default value of the arguments if the argument is not mentioned.
3. **Strictly Adhere to Function Arguments**: Strictly follow the arguments for each individual function, using the default value of the arguments if the argument is not mentioned.
4. **Generate Valid JSON**: Only respond with a ULE File in JSON format as described below and ensure the JSON object can be parsed by Python's `json.loads` (e.g., no trailing commas, no single quotes, etc.).
5. **Use Only Input Words**: Only use words that appear in the input experimental procedure. If the value of an argument is not mentioned in the input experimental procedure, you are forbidden to generate the value of the argument.
6. **Handle Non-standard Characters**: Normalize units to handle non-standard characters without changing the nature of the unit. For example, replace "mL−1" with "mg/mL" and ensure all minus signs are standard ASCII characters. Maintain the original units as they appear in the input, such as keeping "420μL" as "420μL" without converting to other units like "0.42mL".
##############

##############
**Experimental Operation Knowledge**:
1. **Perform One Action at a Time**: Perform one action at a time on only one reagent or reactor. For example, if the raw text is "wash with A and B," the order is washing with A and then washing with B.
2. **Order of Chemical Reactions**: The order of chemical reactions is crucial. For example, if the raw text is "adding A to a solution of B and C in D," the order is adding solvent D to reactor 1, adding reagent B to reactor 1, adding reagent C to reactor 1, and then adding A to reactor 1.
3. **Complete Purification Process**: The full purification process with the precipitation method refers to three steps in sequence: precipitate, filtration, and wash solid. If the repeat times of the purification process are twice, you should call in sequence: precipitate, filtration, wash solid, precipitate, filtration, wash solid, but not precipitate, precipitate, filtration, filtration, wash solid, wash solid. In each function, the repeat times is 1.
4. **Concentration Representation**: The capital M represents concentration, which is equal to mol/L.
5. **Reuse of the Compounds Synthesized in the Procedure**: The procedure can involve the synthesis of several compounds. The synthesized compounds can be used within the same procedure. In this case, determine which reactors the compounds are, and use TransferLiquid or TransferSolid to use them. One example is when the raw text is "The turbid liquid was sealed in a 23 ml Teflon lined autoclave," determine which container the turbid liquid was in during the previous step. If it is not already in the Teflon lined autoclave, you need to call the function "TransferLiquid" to transfer the turbid liquid from the original container to the Teflon lined autoclave.
6. **Stirring and Heating**: When the operation "stir" or "agitate" occurs with other operations, like "agitate and heat," you should call the function "AdjustTemperatureTo" or "AdjustTemperatureFor" according to the description, but not call the function "StirForDuration."
7. **Stock Solution**: If there are any stock solutions mentioned in the context, treat them as existing compounds that have already been prepared by us, without the need for special preparation.
##############

##############
ULE File Format:
{{  "reactants": [
    {{
        "reactant": "<name of the reactant>"
    }},
    {{
        "reactant": "<name of the reactant>"
    }},
    ...
    ],
    "function":[
    {{
        "function_name": "<function name>",
        "function_args":{{
            "<arg name>": "<value>",
            "<arg name>": "<value>"
            ...
            }}
        ...
    }},
    {{
        "function_name": "<function name>",
        "function_args":{{
            "<arg name>": "<value>",
            "<arg name>": "<value>"
            ...
            }}
        ...
    }}
    ...
    ]
}}
##############

"""

semantic_prompt = """
###############
Identify the precise segment in the provided natural language (NL) text that corresponds to the following function and its arguments:
Function Name: {function_name}
Function Arguments: {function_args}
Here is the predefined function set for consistency checking in the double quotes: "{function_set}"
NL text: {NL}
Please extract the exact sentence from the NL text that corresponds to the function and its arguments.
################

##############
**Syntax rules used in the previous process that converts NL to the function and arguments**:
1. **Read and Parse Input**: First, read all the input experimental procedures, then carefully parse all synthetic actions.
2. **Argument Selection Priority**: If an argument can be selected from Single value, Range, or Descriptive string, the priority is Single value > Range > Descriptive string. Use the default value of the arguments if the argument is not mentioned.
3. **Strictly Adhere to Function Arguments**: Strictly follow the arguments for each individual function, using the default value of the arguments if the argument is not mentioned.
4. **Generate Valid JSON**: Only respond with a ULE File in JSON format as described below and ensure the JSON object can be parsed by Python's `json.loads` (e.g., no trailing commas, no single quotes, etc.).
5. **Use Only Input Words**: Only use words that appear in the input experimental procedure. If the value of an argument is not mentioned in the input experimental procedure, you are forbidden to generate the value of the argument.
6. **Handle Non-standard Characters**: Normalize units to handle non-standard characters without changing the nature of the unit. For example, replace "mL−1" with "mg/mL" and ensure all minus signs are standard ASCII characters. Maintain the original units as they appear in the input, such as keeping "420μL" as "420μL" without converting to other units like "0.42mL".
##############

##############
**Experimental operation knowledge used in the process that converts NL to the function and arguments**:
1. **Perform One Action at a Time**: Perform one action at a time on only one reagent or reactor. For example, if the raw text is "wash with A and B," the order is washing with A and then washing with B.
2. **Order of Chemical Reactions**: The order of chemical reactions is crucial. For example, if the raw text is "adding A to a solution of B and C in D," the order is adding solvent D to reactor 1, adding reagent B to reactor 1, adding reagent C to reactor 1, and then adding A to reactor 1.
3. **Complete Purification Process**: The full purification process with the precipitation method refers to three steps in sequence: precipitate, filtration, and wash solid. If the repeat times of the purification process are twice, you should call in sequence: precipitate, filtration, wash solid, precipitate, filtration, wash solid, but not precipitate, precipitate, filtration, filtration, wash solid, wash solid. In each function, the repeat times is 1.
4. **Concentration Representation**: The capital M represents concentration, which is equal to mol/L.
5. **Transfer Liquid**: When the raw text is "The turbid liquid was sealed in a 23 ml Teflon lined autoclave," determine which container the turbid liquid was in during the previous step. If it is not already in the Teflon lined autoclave, you need to call the function "TransferLiquid" to transfer the turbid liquid from the original container to the Teflon lined autoclave.
6. **Stirring and Heating**: When the operation "stir" or "agitate" occurs with other operations, like "agitate and heat," you should call the function "AdjustTemperatureTo" or "AdjustTemperatureFor" according to the description, but not call the function "StirForDuration."
7. **Stock Solution**: If there are any stock solutions mentioned in the context, treat them as existing compounds that have already been prepared by us, without the need for special preparation.
##############
"""
