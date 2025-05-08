from fastapi import FastAPI, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Union
import os
import glob
import json
from NL2CodeWebApp.utilities import b_convert_NL_to_code
from pydantic import BaseModel
from threading import Thread

# find the path
def find_json_files(directory):
    json_files = []
    for root, _, _ in os.walk(directory):
        json_files.extend(glob.glob(os.path.join(root, "*.json")))
    return json_files

# get the examples
reference_folder = "<directory of examples>"
json_files = find_json_files(reference_folder)
examples_total = ""
Examples = """
#### Examples {i}:
- Natural Language Description:
{NL}
- ULE file:
{data}
"""
for i in range(len(json_files)):
    with open(json_files[i], "r", encoding="utf-8") as file:
        data = json.load(file)
    NL = data.pop("NL")
    examples_total = examples_total + Examples.format(i=i + 1, NL=NL, data=data)

# define api keys for the app
api_keys = [
    "<input your api key here>"
] 

# define the API key
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")  # use token authentication
def api_key_auth(api_key: str = Depends(oauth2_scheme)):
    if api_key not in api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden"
        )

app = FastAPI()

# define the root method
@app.get("/", dependencies=[Depends(api_key_auth)])
def read_root():
    return {"Hello": "World"}

# define the input and the NL to code function 
class Context(BaseModel):
    context: str
    
@app.post("/NLToCodeSubmit/",dependencies=[Depends(api_key_auth)])
async def submit_conversion(args: Context):
    """
    Perform the conversion and return the codes in json format.
    """
    # set a global variable to restore the content 
    global results
    results = {"code_generated": None, "results": None}
    
    # get the context to be converted
    exp_NL = args.context
    thread = Thread(target=b_convert_NL_to_code, args=(exp_NL, str(None), results, 3, examples_total))
    thread.start()
    return {"response": "The task has been submitted successfully. It is recommended to check it again in 1 minute!"}

@app.get("/NLToCodoResult/",dependencies=[Depends(api_key_auth)])
async def check_results():
    """
    Perform the conversion and return the codes in json format.
    """
    try:
        if results["code_generated"] == None:
            return {"Code": "The task has been submitted successfully but not finished yet. Check it again later."}
        elif results["code_generated"] == True:
            return {"Code": results["results"]}
        elif results["code_generated"] == False:
            return {"Code": "The process to convert the natural language to code has failed. Ask the user to check the procedure."}
    except:
        return {"Code": "There is an server error as the results are not defined. It indicates no task has been submitted before."}