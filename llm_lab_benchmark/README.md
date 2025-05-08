# llm_lab_benchmark

## Overview

This repository contains resources and code for developing and benchmarking workflows that convert chemical synthesis procedures written in natural language into structured unit operations.

## Getting Started

To get started with the package for benchmark, follow these steps:

Install the [llmlab](./llmlab) package used in the benchmark:

   ```bash
   pip install -e .
   ```
Note to fill the api keys in [constant.py](./llmlab/constant.py) before using the services from OpenAI api and the ChemSpide.
```bash
open_ai_api_key = "<input your api key here>"
chemspider_api_key = '<input your api key here>'
```

[examples](./benchmark_dataset/examples.json) are generated codes from natural language during benchmark.

[inorganic](./benchmark_dataset/inorganic_processed.json)/[organic](./benchmark_dataset/organic.json) are chemical synthesis procedures to evaluate the coverage of the unit operations. 

## Detailed Description
One example can be found at [here](./example/), where the natural language is written in the [xlsx file](./example/exp-easy.xlsx), with empty notes. If needed, the notes should be filled. The [jupyter-notebook](./example/batch_test.ipynb) was used to convert the language to code. 

For more detailed information, please refer to the original paper and its supplementary information section 2.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For any questions or inquiries, please contact us at yibin_jiang@outlook.com.
