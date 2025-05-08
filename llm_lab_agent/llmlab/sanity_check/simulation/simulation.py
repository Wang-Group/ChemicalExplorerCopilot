from llmlab.graph import exp_graph
from llmlab.operations.exp_operation.basic_step import BasicStep
from typing import List

def simulate_exp(reactors: List[str], parsed_functions = List[BasicStep]):
    """
    Execute the simulation accoridng to the parsed functions
    """
    # define an experimental graph 
    graph = exp_graph(reactors = reactors)
    reactor_content = []
    
    # execute simulations 
    for step in parsed_functions:
        print(step)
        step.sim_execute(graph = graph)
        # record the contents inside the reactors (Liquid in mL, Solid in g) 
        reactor_content.append(graph.get_reactor_content())

    # record the scale factor 
    scale_factor = []
    for i in reactor_content:
        for key, value in i.items():
            if key != "waste":
                scale_factor.append(value[0]/(graph.reactors[key].maximum_volume))
            
    return reactor_content, max(scale_factor)
