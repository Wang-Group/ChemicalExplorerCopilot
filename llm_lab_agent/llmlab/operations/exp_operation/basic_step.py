from llmlab.graph import exp_graph
import inspect
from copy import copy 

class BasicStep:

    def __init__(self, **args) -> None:
        """
        Create a dict to store the quantity that is ambiguous
        """
        self.ambiguity_dict = {}
        self.mandatory_args, self.optional_args = self.get_argument_info()
        
    def sim_execute(self, graph: exp_graph):
        return 
    
    def execute(self):
        return 
    
    def get_argument_info(self):
        signature = inspect.signature(self.__init__)
        mandatory_args = [param.name for param in signature.parameters.values() if param.default == param.empty]
        optional_args = [param.name for param in signature.parameters.values() if param.default != param.empty]
        return mandatory_args, optional_args
    
    def translate_NL(self):
        """"the default NL representation of a step"""
        return "The natural language representation of current step is not supported and will be skipped."
    
    def check_ambiguity(self, mode = "plain_txt"):
        return "Ambiguity check of current step is not supported and will be skipped."

    def rescale(self, rescale_factor: float):
        """
        Change the extensive property according to a rescale_factor 
        """
        return  
    
    def to_dict(self):
        pass 

    def convert_molar_units(self):
        pass 