import sys
import re
from random import uniform
from utils.qubo_utils import tangle_problem
from utils.graph_utils import graph_from_file

if __name__ == "__main__":
    filename = sys.argv[1]
    graph = graph_from_file(filename)
    
    # Hacky weight assignment
    for node in graph.nodes:
        if re.search("^c\d*$", node):
            graph.nodes[node]["weight"] = 1
        elif re.search("^r", node):
            graph.nodes[node]["weight"] = 2
        elif re.search("^a1c\d*$", node):
            graph.nodes[node]["weight"] = 1
        elif re.search("i\d", node):
            graph.nodes[node]["weight"] = 1 if uniform(0, 1) > 0.5 else 0
        else:
            graph.nodes[node]["weight"] = 0
            
    sample, energy, lamda, mu = tangle_problem(graph)