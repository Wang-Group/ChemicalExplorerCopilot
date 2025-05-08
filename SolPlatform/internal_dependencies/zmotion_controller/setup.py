from distutils.core import setup
from setuptools import find_packages

setup(
    name="zmotion",
    version="1.0.0",
    description="the toolbox to control Zmotion_controller",
    author="Enyu He, Yuanxiang Ye, Lin Huang",
    author_email="409476555@qq.com",
    packages=find_packages(),
    install_requires=[
        "ctype"
    ], 
    include_package_data = True, 
    package_data = {
        '': ['*.dll']
    }
)
