from distutils.core import setup
from setuptools import find_packages

setup(
    name="NL2CodeWebApp",
    version="1.0.0",
    description="agent to convert the description of chemical synthesis to an executable code",
    author="Yibin Jiang",
    author_email="yibin_jiang@outlook.com",
    packages=find_packages(),
    install_requires=[
        "langchain_community",
        "tiktoken",
        "langchain-openai",
        "langchainhub",
        "chromadb",
        "langchain",
        "langgraph",
        "tavily-python",
    ],
    include_package_data=True,
    package_data={
        '': ['*.txt'],
    },
)
