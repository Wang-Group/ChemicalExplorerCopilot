from distutils.core import setup
from setuptools import find_packages

setup(
    name="MS_hotplate",
    version="1.0.0",
    description="the toolbox to control MS-H hotplates",
    author="Chao Zhang, Yibin Jiang, Lin Huang",
    author_email="Zhangchao@henu.edu.cn,yibin_jiang@outlook.com",
    packages=find_packages(),
    install_requires=[
        "pyserial>=3.4"
    ]
)
