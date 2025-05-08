from setuptools import setup
from setuptools import find_packages

setup(
    name="SolPlatform",
    version="1.0.0",
    description="the toolbox to control SolPlatform",
    author="Lin Huang, Enyu He, Yibin Jiang",
    author_email="yibin_jiang@outlook.com",
    packages=find_packages(),
    install_requires=[
        "zeep"
    ]
)
