import gurobipy as gp
from gurobipy import GRB
import numpy as np
import sys
import re
import os
from datetime import datetime
from random import uniform
from utils.qubo_utils import graph_to_max_path_digraph, max_path_problem_qubo_matrix
from utils.graph_utils import graph_from_gfa_file, toy_graph, normalise_node_weights
from utils.sampling_utils import get_max_path_problem_path_from_gurobi


if len(sys.argv) > 1:
    filename = sys.argv[1]
    graph = graph_from_gfa_file(filename)

    try:
        for node in graph.nodes:
            graph.nodes[node]["weight"]
    except KeyError:
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
    
else:
    filename = 'toy'
    graph = toy_graph(exact_solution=True)

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
    
if len(sys.argv) > 3:
    try:
        time_limit = int(sys.argv[3])
    except ValueError:
        time_limit = 60
else:
    time_limit = 60

dg = graph_to_max_path_digraph(graph)
W = len(dg.nodes) - 1
penalty = W

qubo_matrix = max_path_problem_qubo_matrix(dg, penalty)

# Write to MQLib Format
non_zero = np.nonzero(qubo_matrix)
non_zero_count = int(non_zero[0].shape[0] / 2 + qubo_matrix.shape[0] / 2)
f = open(f'out/mqlib_qubo_{os.path.basename(filename)}.txt', 'w')
f.write(f'{qubo_matrix.shape[0]} {non_zero_count}\n')
for i in range(qubo_matrix.shape[0]):
    for j in range(i, qubo_matrix.shape[0]):
        if not qubo_matrix[i, j] == 0: 
            f.write(f'{i + 1} {j + 1} {-qubo_matrix[i, j]}\n')
    
offset = penalty * (W + 3)

with gp.Env() as env, gp.Model(env=env) as model:
    vars = model.addMVar(shape=qubo_matrix.shape[0], vtype=GRB.BINARY, name="x")
    model.setObjective(vars @ qubo_matrix @ vars, GRB.MINIMIZE)
    model.Params.BestObjStop = -W - offset + 1
    model.Params.MIPFocus = 1
    model.Params.ImproveStartTime = 1200
    model.Params.TimeLimit = time_limit
    model.optimize()
    
    path = get_max_path_problem_path_from_gurobi(vars.X, dg)
    print(vars.X)
    print(path)
    print('Obj: %g' % model.ObjVal)
    print(f'Offset: {offset}')
    print(f'Best possible score: {-W - offset + 1}')
    
    save_dir = "out"
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
        
    now = datetime.now().strftime("%d%m%Y_%H%M")
    save_file = save_dir + f"/qubo_path_gurobi_{now}"   
        
    to_save = np.array([vars.X, model.ObjVal + offset, path], dtype=object)
    np.save(save_file, to_save)