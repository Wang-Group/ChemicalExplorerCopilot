from distutils.core import setup
from setuptools import find_packages

setup(
    name="llmlab",
    version="1.0.0",
    description="use LLM to write synthesis codes to control robots",
    author="Yibin Jiang",
    author_email="yibin_jiang@outlook.com",
    packages=find_packages(),
    install_requires=[
        "pyserial>=3.4",
        "pubchempy",
        "openai",
        "chemspipy",
        "numpy",
    ],
    include_package_data=True,
    package_data={
        '': ['*.txt'],
    },
)
