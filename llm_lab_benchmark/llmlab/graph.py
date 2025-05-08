import networkx as nx
from llmlab.utlis.property import Reactor
from copy import copy 

class exp_graph:
    """
    An experimental graph object
    Args:
        reactors: a list of names of the reactors
    """
    def __init__(self, reactors: list):

        self.reactors = {}
        for reactor_name in reactors:
            self.reactors[reactor_name] = Reactor(reactor_name = reactor_name)
             
    def get_reactor_content(self):
        """
        Return the amount of liquid (in mL) and solid (in g) inside each of the reactor.  
        """
        # the total amount of liquid/solid inside reactors
        reactor_total_amount = {}
        for reactor_name, reactor in self.reactors.items():
            reactor_total_amount[reactor_name] = reactor.total_amount()
            
        return reactor_total_amount