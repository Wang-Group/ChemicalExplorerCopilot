from distutils.core import setup
from setuptools import find_packages

setup(
    name="leadshine_driver",
    version="1.0.0",
    description="the toolbox for the control of leadshine_stepper_driver",
    author="Lin_huang",
    author_email = "Lin_huang1757@gmail.com",
    packages = find_packages(),
    install_requires = [
        "pyserial>=3.4", 
        "crcmod"
    ]
)
