from distutils.core import setup
from setuptools import find_packages

setup(
    name="pHTestuino",
    version="1.0.0",
    description="the toolbox to control pHMeter",
    author="Lin Huang, Yibin Jiang",
    author_email="Lin_huang1757@gmail.com",
    packages=find_packages(),
    install_requires=[
        'sympy', 
    ]
)
