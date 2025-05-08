"""
.. module:: steps.collection
    :platforms: Unix, Windows
    :synopsis: Collection of step names and values associated to each step

"""

from typing import Dict
from . import steps_base

from xdl.steps import special_steps

import copy
import inspect

#: Dictionary of base step name keys and step class values.
BASE_STEP_OBJ_DICT: Dict[str, type] = {
    m[0]: m[1] for m in inspect.getmembers(steps_base, inspect.isclass)
}

#: Dictionary of all step name keys and step class values.
STEP_OBJ_DICT: Dict[str, type] = copy.copy(BASE_STEP_OBJ_DICT)