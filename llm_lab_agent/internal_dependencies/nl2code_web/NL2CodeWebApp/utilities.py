import numpy as np
import pandas as pd
from llmlab.check_one_round import prepare_one_batch_messages, send_messages, convert_finished_batch, validate_finished_batch
import json
from llmlab.converter.llm_link.NL_manager import NLManager

def b_convert_NL_to_code(NL, notes, results, maximum_try_num = 3, reference_samples = None):
    """
    Convert the natural language to a robotic-executable code
    Args:
        NL: the chemical synthesis 
        maximum_try_num: the maximum try num for the LLM model to convert the code 
    Return: 
        bool, if the conversion is successful 
    """
    # define the initial pd
    content = pd.DataFrame(
        {
            "NL": NL,
            "Notes": notes,
            "chat_history": None,
            "function_info": None,
            "total_errors": None,
            "gpt_generated": None,
            "count": np.zeros(1),
            "pass": np.zeros(1).astype("bool"),
        }
    )
    # convert all None object to empty list
    content = content.applymap(lambda x: [] if x is None else x)
    
    for iteration_num in range(maximum_try_num):
        
        # prepare the messages to be sent, update the content file, and save the jsonl to task_file_name
        content, task_file_name = prepare_one_batch_messages(content, reference_samples = reference_samples)
        
        # # actually upload the file to the openAI api
        submitted_task_path, batch_job_id = send_messages(task_file_name)
        # define the path to save the results 
        result_path = f"./{batch_job_id}.jsonl"
        
        # check if the job is finished or not 
        result_path, result = convert_finished_batch(batch_job_id, result_path)
        
        # perform check of the results
        content = validate_finished_batch(content, result_path)
        # save the content for the current iteration
        content.to_excel(f"./iter_{iteration_num}.xlsx")
        
        # if everything is right, we should stop the processing 
        if (content["pass"].sum()) == len(content["pass"]):
            results["code_generated"] = True
            results["results"] = content["gpt_generated"].iloc[0][-1]
            return 
        
    results["code_generated"] = False
    results["results"] = None
    return 