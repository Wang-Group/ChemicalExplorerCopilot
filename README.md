# ChemicalExplorerCopilot
![](./Photos/whole_platform.JPG)

This repo introduces an integrated multifunctional chemical experiment assistant designed to enhance experimental efficiency and accuracy through various modules. The relavent content is described in the paper ["Natural-Language-Interfaced Robotic Synthesis for AI-Copilot-Assisted Exploration of Inorganic Materials"](./). Below is a detailed description of each folder for the contents of the paper.

# Software Requirements

This software requires the following:
* Python 3.11. It is recommended to use [Anaconda](https://anaconda.org/) to manage the python environment, with common modules installed automatically.
   ```bash
   conda create -n yourenvname python=3.11 anaconda
   ```
* [SolPlatform](./SolPlatform/) for hardware control of the system.
* [llmlab benchmark version](./llm_lab_benchmark/) for converting langauge to code, without webapp.
* [llmlab agent version](./llm_lab_agent/) for converting langauge to code with webapp, which can be accessed by GPTs from OpenAI. 

Note: [llmlab benchmark version](./llm_lab_benchmark/) and [llmlab agent version](./llm_lab_agent/) will both be called as llmlab. It is recommended to use different environments for them. 

## Solplatform
[Solplatform](./SolPlatform) is responsible for hardware control with experiment logs recorded. It is integrated with the llmlab package (see below) that performed the sanity check for the generated codes. 

## llm_lab_benchmark
The [llm_lab_benchmark](./llm_lab_benchmark) folder used large language models (LLM, gpt-4 and gpt-4o here) to convert natural language into machine-executable code. It includes the following content:
1. [llmlab](./llm_lab_benchmark/llmlab/) package, which is for:
    - **Natural Language Conversion**: Convert natural language instructions from experimenters into executable experimental code.
    - **Syntax Check**: Check for syntax errors in the generated code for validation.
    - **Ambiguity Detection**: Analyze code logic to identify potential errors, and plan for experiments.

2. a collection of [66 examples](./llm_lab_benchmark/benchmark_dataset/examples.json) of generated codes from natural language during benchmark.

3. a collection of [inorganic](./llm_lab_benchmark/benchmark_dataset/inorganic_processed.json)/[organic](./llm_lab_benchmark/benchmark_dataset/organic.json) synthesis procedures to evaluate the coverage of the unit operations.

This repo is originally used to develop the workflow. Once the workflow is complete, its functionality is transferred to [llm_lab_agent](./llm_lab_agent), wrapped by FastAPI to be interfaced by the AI agent constructed by the GPT store feature from OpenAI. 

## chat_record
[chat_record](./chat_record) records interactions between humans and AI.

