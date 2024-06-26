import sys
import re
import os
import numpy as np
from datetime import datetime
from random import uniform
from dwave.system import LeapHybridSampler
from dimod.reference import SimulatedAnnealingSampler
from utils.qubo_utils import max_path_problem
from utils.graph_utils import graph_from_gfa_file, toy_graph, normalise_node_weights

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        graph = graph_from_gfa_file(filename)
        
        # # Real weight assignment
        # for node in graph.nodes:
        #     if re.search("^c\d*$", node):
        #         graph.nodes[node]["weight"] = 1
        #     elif re.search("^a1c\d*$", node):
        #         graph.nodes[node]["weight"] = 1
        #     elif re.search("^c6a1*$", node):
        #         graph.nodes[node]["weight"] = 1
        #     elif re.search("^cnv*$", node):
        #         graph.nodes[node]["weight"] = 3
        #     elif re.search("^cnvlink*$", node):
        #         graph.nodes[node]["weight"] = 1
        #     elif re.search("^cnvstr*$", node):
        #         graph.nodes[node]["weight"] = 26
        #     else:
        #         graph.nodes[node]["weight"] = 0
        
        # graph.nodes['rCT']["weight"] = 20
        # graph.nodes['rCA']["weight"] = 26
        # graph.nodes['r16']["weight"] = 3
        # graph.nodes['a1i0']["weight"] = 1
        # graph.nodes['i5']["weight"] = 1
        
        try:
            for node in graph.nodes:
                graph.nodes[node]["weight"]
        except KeyError:
            # Arbitrary weight assignment
            for node in graph.nodes:
                if re.search("^c\d*$", node):
                    graph.nodes[node]["weight"] = 1
                elif re.search("^r", node):
                    graph.nodes[node]["weight"] = 2
                elif re.search("^a1c\d*$", node):
                    graph.nodes[node]["weight"] = 1
                elif re.search("^c6a1*$", node):
                    graph.nodes[node]["weight"] = 1
                elif re.search("^cnv*$", node):
                    graph.nodes[node]["weight"] = 3
                elif re.search("^cnvlink*$", node):
                    graph.nodes[node]["weight"] = 1
                elif re.search("^cnvstr*$", node):
                    graph.nodes[node]["weight"] = 5
                elif re.search("i\d", node):
                    graph.nodes[node]["weight"] = 1 if uniform(0, 1) > 0.5 else 0
                else:
                    graph.nodes[node]["weight"] = 0
    
    else:
        graph = toy_graph(exact_solution=False)
    
    if len(sys.argv) > 2:
        print('Trying to normalise')
        try:
            normalisation = int(sys.argv[2])
            print(f'Normalising by {normalisation}')
            graph = normalise_node_weights(graph, normalisation)
        except ValueError:
            graph = normalise_node_weights(graph, 1)
    else:
        graph = normalise_node_weights(graph, 1)
        
    print(list(zip(list(graph.nodes), [graph.nodes[node]["normalised_weight"] for node in graph.nodes])))
    
    if len(sys.argv) > 3 and sys.argv[3] == 'q':
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
    for i in range(len(path) - 1):
        v1 = path[i][1][0:-2]
        v2 = path[i + 1][1][0:-2]
        if not (v1, v2) in graph.edges and not path[i + 1][1] == 'end':
            print(f'Broke graph edge at step {i}')
    
    save_dir = "out"
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
        
    now = datetime.now().strftime("%d%m%Y_%H%M")
    save_file = save_dir + f"/qubo_path_{solver}_{now}"   
        
    to_save = np.array([sample, energy, path], dtype=object)
    np.save(save_file, to_save)