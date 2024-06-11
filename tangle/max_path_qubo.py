import sys
import re
import os
import numpy as np
from datetime import datetime
from random import uniform
from dwave.system import LeapHybridSampler
from dimod.reference import SimulatedAnnealingSampler
from utils.qubo_utils import max_path_problem, _max_path_problem_qubo_matrix
from utils.graph_utils import graph_from_gfa_file, toy_graph

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        graph = graph_from_gfa_file(filename)
    
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
                graph.nodes[node] = 0
    
    else:
        graph = toy_graph(exact_solution=False)
    
    print(list(zip(list(graph.nodes), [graph.nodes[node]["weight"] for node in graph.nodes])))
    
    if len(sys.argv) > 2 and sys.argv[2] == 'q':
        solver = "quantum"
        sampler = LeapHybridSampler()
        print("Using Leap Hybrid Solver")
    else:
        solver = "classical"
        sampler = SimulatedAnnealingSampler()
        print("Using Classical Solver")    
   
    sample, energy, path = max_path_problem(graph, sampler)
    
    print(f"Best path: {path}")
    print(f"Energy of path: {energy}")
    
    save_dir = "out"
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
        
    now = datetime.now().strftime("%d%m%Y_%H%M")
    save_file = save_dir + f"/qubo_path_{solver}_{now}"   
        
    to_save = np.array([sample, energy, path], dtype=object)
    np.save(save_file, to_save)