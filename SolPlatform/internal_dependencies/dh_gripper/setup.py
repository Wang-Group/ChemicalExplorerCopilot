from distutils.core import setup
from setuptools import find_packages

setup(
    name="dh_gripper",
    version="1.0.0",
    description="the toolbox for the control of dh gripper",
    author="Enyu He, Lin Huang",
    author_email = "409476555@qq.com",
    packages = find_packages(),
    install_requires = [
        "pyserial>=3.4", 
        "crcmod"
    ]
)
