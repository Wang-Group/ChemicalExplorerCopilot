"""
.. module:: chemputerxdl.platform
    :platforms: Unix, Windows
    :synopsis: Chemputer XDL abstraction of the Chempiler

"""

from networkx.classes import Graph
from typing import Dict
from .collection import STEP_OBJ_DICT
from xdl.platforms import AbstractPlatform
from xdl.execution import AbstractXDLExecutor

class PlatformManager(AbstractXDLExecutor):
    """Class for controlling the Drivers of the platform

    Args:
        config_file (str): Path to config file for the platform
    """

    def __init__(
        self,
        xdl: 'XDL',
    ) -> None:

        """Initalize ``_xdl`` and ``logger`` member variables."""
        super().__init__()
        
class VirtualPlatform(AbstractPlatform):

    @property
    def step_library(self) -> Dict:
        """Returns the library of steps in the platform.
        Returns:
            Dict: Step library
        """

        return STEP_OBJ_DICT

    @property
    def executor(self) -> PlatformManager:
        """Get the executor of the platform

        Returns:
            ChemputerExecutor: Chemputer Executor
        """

        return PlatformManager
