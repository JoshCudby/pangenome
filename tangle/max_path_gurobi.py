import gurobipy as gp
from gurobipy import GRB
import numpy as np
import sys
import re
from random import uniform
from utils.qubo_utils import graph_to_max_path_digraph, _max_path_problem_qubo_matrix
from utils.graph_utils import graph_from_gfa_file, toy_graph
from utils.sampling_utils import get_max_path_problem_path_from_gurobi


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
                graph.nodes[node]["weight"] = 0
    
else:
    graph = toy_graph(exact_solution=True)

print(list(zip(list(graph.nodes), [graph.nodes[node]["weight"] for node in graph.nodes])))

dg = graph_to_max_path_digraph(graph)
W = len(dg.nodes) - 1
penalty = W

qubo_matrix = _max_path_problem_qubo_matrix(dg, penalty)
offset = penalty * (W + 3)

with gp.Env() as env, gp.Model(env=env) as model:
    vars = model.addMVar(shape=qubo_matrix.shape[0], vtype=GRB.BINARY, name="x")
    model.setObjective(vars @ qubo_matrix @ vars, GRB.MINIMIZE)
    model.Params.BestObjStop = -W - offset + 1
    model.Params.MIPFocus = 1
    model.Params.ImproveStartTime = 1200
    model.optimize()
    
    print(vars.X)
    print(get_max_path_problem_path_from_gurobi(vars.X, dg))
    print('Obj: %g' % model.ObjVal)
    print(f'Offset: {offset}')
    print(f'Best possible score: {-W - offset + 1}')