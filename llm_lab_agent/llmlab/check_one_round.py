import pkg_resources
from llmlab.verify import validate_properties
from llmlab.converter.llm_link import NLManager
from llmlab.llm.prompt_test import initial_prompt, iter_prompt
from llmlab.utlis.gpt import (
    get_completion,
    iter_completion,
)
from llmlab.sanity_check.syntax.response_to_function import parse_json
from llmlab.utlis.syntax import save_to_json, write_jsonl, write_json
import pandas as pd
import datetime
import openai
import shutil
import time
import json
import os 
from copy import deepcopy

function_set_path = pkg_resources.resource_filename("llmlab", "/llm/function_set.txt")
with open(function_set_path, "r", encoding="utf-8") as f:
    FUNCTION_SET = f.read()

reference_path = pkg_resources.resource_filename("llmlab", "/llm/reference_samples.txt")
with open(reference_path, "r", encoding="utf-8") as f:
    REFERENCE_SAMPLE = f.read()

Materials_Path = pkg_resources.resource_filename("llmlab", "/materials.json")


def wait_for_batch_completion(batch_job_id, check_interval=10):
    """
    Wait for the batch job to complete.
    Args:
        batch_job_id (str): The ID of the batch job.
        check_interval (int): Time interval (in seconds) between status checks. 
    Returns:
        dict: The completed batch job information.
    """
    while True:
        batch_job = openai.batches.retrieve(batch_job_id)
        if batch_job.status == "completed":
            print("Batch process completed.", flush = True)
            return batch_job
        elif batch_job.status == "failed":
            raise Exception("Batch process failed.")

        print(
            f"Current status: {batch_job.status}. Checking again in {check_interval} seconds...", flush = True
        )
        time.sleep(check_interval)


def send_to_gpt(
    count, NL, model, CHAT_HISTORY, FUNCTION_INFO_GLOBAL, total_errors, sent=True, reference_samples = None
):
    """
    Send the content fo the gpt models and get responses.
    Args:
        count: the number of iteration that the model is trying to convert teh NL
        NL: the natural language description that should be converted
        model: the name of the model, e.g., "gpt-4o"
        CHAT_HISTORY: the chat history of the model, a list.
        FUNCTION_INFO_GLOBAL: all the json str or json object that the model returns
        total_errors: all the erros during the interaction
        sent: if True, send the message and return the response. if False, return the content to be sent
    Return:
        to_send: the content that should be sent to the model.
        gpt_response: the response from the model
    """
    # prompt according the iteration number
    if count == 0:
        to_send = initial_prompt.format(
            function_set=FUNCTION_SET, reference_samples=reference_samples
        )
        if sent == False:
            return get_completion(
                to_send, NL, model, CHAT_HISTORY=None, message_only=True
            )
        else:
            gpt_response = get_completion(to_send, NL, model, CHAT_HISTORY)
            return gpt_response
    else:
        to_send = iter_prompt.format(
            json_object=FUNCTION_INFO_GLOBAL[-1],
            error=total_errors[-1],
            function_set=FUNCTION_SET,
            reference_samples=reference_samples,
        )
        if sent == False:
            return iter_completion(
                to_send, NL, model, CHAT_HISTORY=None, message_only=True
            )
        else:
            gpt_response = iter_completion(to_send, NL, model, CHAT_HISTORY)
            return gpt_response


def one_round_check(gpt_response, FUNCTION_INFO_GLOBAL, NL, gpt_generated):
    """
    Ask the LLM to create a set of instructions according to the function set and the nature language
    Args:
        count: the times the model is trying.
        NL: the natural language that should be processed
        total_errors: the errors occured previously
        model: the name of the models
    """
    # convert the response to json object (it should be json_parseable)
    json_str = gpt_response
    try:
        # check and convert the response string to a dictionary
        json_dict = parse_json(json_str)

        # add this json to the funciton collection
        FUNCTION_INFO_GLOBAL.append(json_dict)
        gpt_generated.append(deepcopy(json_dict))

        # copy this json, add NL to it and save it 
        json_to_save = deepcopy(json_dict)
        json_to_save["NL"] = NL
        Json_Path = save_to_json(json_to_save, working_path="./temp")

    except:
        # add this json str to the funciton collection
        gpt_generated.append(deepcopy(json_str))
        FUNCTION_INFO_GLOBAL.append(json_str)
        raise ValueError(
            f"""Converting the responded "json string" to a json object failed."""
        )

    # validate the properties
    errors = validate_properties(json_dict)
    if errors:
        raise ValueError(
            f"Error occured during checking the properties of the function set. The error is listed below: {errors}"
        )

    # initialize a manager object
    json_mng = NLManager(
        materials_path=Materials_Path, json_path=Json_Path, logger=None
    )
    json_mng.parse_function_set()  # parse to functions, which is a more strict checking of the function set
    if json_mng.errors:
        raise ValueError(
            f"Error occured during defining the functions. The error is listed below: {json_mng.errors}"
        )

    # get the function information of the current functions before unit check, to see if the meaning is right
    FUNCITON_INFO = json_mng.acquire_current_parsed_functions()

    # replace this json (converted properly) to the funciton collection (replace the last element only)
    FUNCTION_INFO_GLOBAL[-1] = FUNCITON_INFO

    # FIXME in the future
    # semantic_check(FUNCITON_INFO, NL, model, FUNCTION_SET)

    # check if the unit is right, if not right, raise value error directly.
    json_mng.get_function_set()  # get the function set before unit check as it relies on the function set
    json_mng.convert_property_to_standard_unit(raise_error_directly=True)

    # if everything passes, we will return the mng object, and recover dict from it.
    return json_mng, Json_Path


def NL2P_interactive(
    NL: str,
    maximum_tries: int = 3,
    model: str = "gpt-4o",
    CHAT_HISTORY=[],
    FUNCTION_INFO_GLOBAL=[],
    total_errors=[],
):
    """
    Iterate maximum_count amount of times to convert nature language to a structured instructions.
    Args:
        NL: str, a natural language.
        maximum_count: int, the maximum amount of times to try.
        model: the name of the model to use
    """
    for count in range(maximum_tries):
        try:
            # get the response
            gpt_response = send_to_gpt(
                count,
                NL,
                model,
                CHAT_HISTORY,
                FUNCTION_INFO_GLOBAL,
                total_errors,
                sent=True,
            )
            # validate the response
            json_mng = one_round_check(gpt_response, FUNCTION_INFO_GLOBAL)
            # export the results
            json_out = json_mng.acquire_current_parsed_functions()
            out_dict = {}
            out_dict["NL"] = NL
            out_dict["function"] = json_out
            return out_dict, CHAT_HISTORY

        except Exception as e:
            total_errors.append(str(e))
            print(count, total_errors[-1], flush = True)

    return False


def prepare_one_batch_messages(content: pd.DataFrame, model: str = "gpt-4o", reference_samples = None):
    """
    Ask the LLM to create a set of instructions according to the function set and the nature language by a batch of things to send
    Args:
        content: a pandas framework contaning the content to be send.
        model: the LLM model
    Returns:
        submitted_task_path: the path of the submitted task
    """
    # prepare the messages according to the dataframe
    all_messages = []

    # collect all the messages that should be sent to the model
    for row_index, content_temp in content.iterrows():
        # if it is already processed, pass the current row
        pass_or_not = content_temp["pass"]
        if pass_or_not == True:
            pass
        else:
            # get the contents within the rows
            NL = content_temp["NL"]
            function_info = content_temp["function_info"]
            total_errors = content_temp["total_errors"]
            count = content_temp["count"]
            notes = str(content_temp["Notes"])
            # get the content to send to the model
            message_to_send = send_to_gpt(
                count,
                NL + "\nNotes:" + notes,
                model,
                CHAT_HISTORY=None,  # we are not updating the chat_history as this stage
                FUNCTION_INFO_GLOBAL=function_info,
                total_errors=total_errors,
                sent=False,
                reference_samples = reference_samples
            )
            all_messages.append({"index": row_index, "content": message_to_send})

    # save the jsonl file for all the tasks
    tasks = []
    for message_temp in all_messages:
        # get the row index from the original pandas dataframe
        index = message_temp["index"]
        # set the task of according to the original dataframe
        task = {
            "custom_id": f"task-{index}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": message_temp["content"],
            },
        }
        # append the task
        tasks.append(task)
        # append to the chat history
        content["chat_history"].iloc[index].append(message_temp["content"])

    # define task_file_name
    task_file_name = (
        "./" + datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + ".jsonl"
    )
    write_jsonl(tasks, task_file_name)

    return content, task_file_name


def send_messages(task_file_name):
    """
    Upload the task_file to OpenAI
    """
    # upload the file
    batch_file = openai.files.create(file=open(task_file_name, "rb"), purpose="batch")

    # create the batch job
    batch_job = openai.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )

    # create a file to record the files uploaded with their batch_job_id
    submitted_task_path = task_file_name.replace(
        ".jsonl", "_" + batch_job.id + "_" + ".jsonl"
    )
    while True:
        try:
            shutil.copy2(task_file_name, submitted_task_path)
            break
        except:
            time.sleep(1)

    return submitted_task_path, batch_job.id


def convert_finished_batch(batch_job_id, result_path):
    """
    Convert the finished batch job to results. If the job is not finished yet, wait for it to finish.
    """
    # wait until the whole process is finished by querying the batch_job
    completed_batch_job = wait_for_batch_completion(batch_job_id=batch_job_id)

    # Retrieving results
    result_file_id = completed_batch_job.output_file_id
    result = openai.files.content(result_file_id).content
    # save the result to a local file
    with open(result_path, "wb") as file:
        file.write(result)

    return result_path, result


def validate_finished_batch(content: pd.DataFrame, result_path):
    """
    Read in the responses, and check if it passed the validation. If not, create a new dataframe to store it.
    """
    # read in the json file that corresponding to the data frame
    with open(result_path, "r") as file:
        results = [json.loads(line) for line in file]

    # Reading results
    for res in results:
        # Getting row index from task id
        task_id = res["custom_id"]
        index = int(task_id.split("-")[-1])

        # get the gpt_response
        gpt_response = res["response"]["body"]["choices"][0]["message"]["content"]
        # add one to the current evaluation
        content.loc[index, "count"] += 1

        # get the corresponding row of the dataframe
        content_temp = content.iloc[index]

        # record the chat history for the last conversation (Note this is different from that in NL2P_interactive)
        content_temp["chat_history"][-1].append(
            {"role": "assistant", "content": gpt_response}
        )
        # perform the check and collect error information of the response for that row
        try:
            # validate the response
            json_mng, Json_Path = one_round_check(
                gpt_response, content_temp["function_info"], content_temp["NL"], content_temp["gpt_generated"]
            )  # this handles the function_info automatically
            # if it passes, do nothing and this row is finished
            content.loc[index, "pass"] = True

            json_to_write = {
                "NL": content_temp["NL"], 
                "function": 
                    json_mng.acquire_current_parsed_functions()
                }
            write_json(json_dict = json_to_write, json_path = Json_Path.replace(".json","_final.json"))

        except Exception as e:
            # if there is an error, update the error message to the row
            content_temp["total_errors"].append(str(e))
            assert content.loc[index, "pass"] == False

    # return the updated dataframe to the user to continue
    return content
