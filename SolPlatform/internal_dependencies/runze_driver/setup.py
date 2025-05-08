from setuptools import setup
from setuptools import find_packages

setup(
    name="Runze_driver",
    version="1.0.0",
    description="the toolbox to control Runze devices",
    author="Lin Huang, Enyu He, Xue Wang",
    author_email="Lin_huang1757@gmail.com",
    packages=find_packages(),
    install_requires=[
        "pyserial>=3.4"
    ]
)
