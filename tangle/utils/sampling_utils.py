import numpy as np
import networkx as nx
from math import floor

def get_path(sample: dict):
    return sorted([i for i in list(sample.keys()) if sample[i]], key=lambda e: e[1])


def get_node_visits(sample: dict):
    path = get_path(sample)
    nodes = set([key[0] for key in list(sample.keys())])
    node_visits = {node : 0 for node in nodes}
    for path_node in path:
        node_visits[path_node[0]] += 1
        
    return node_visits


def get_constraint_values(sample: dict, graph: nx.DiGraph):
    node_visits = get_node_visits(sample)
    constraint_values = np.array([node_visits[x] - graph.nodes.data()[x]["weight"] for x in list(graph.nodes)])
    return constraint_values


def _index_to_node_time(idx, nodes):
    rem = idx % nodes
    div = floor(idx / nodes)
    return (div, rem)


def get_max_path_problem_path_from_sample(sample: dict, dg: nx.DiGraph) -> list:
    on_vars = []
    for i in range(len(sample.keys())):
        if sample[i] == 1:
            on_vars.append(i)
    path = [_index_to_node_time(x, len(dg.nodes)) for x in on_vars]
    path = [(e[0], list(dg.nodes)[e[1]]) for e in path]
    return path


def qubo_vars_to_path(qubo_vars: list[int], dg: nx.DiGraph) -> list:
    on_vars = []
    for i, var in enumerate(qubo_vars):
        if var == 1:
            on_vars.append(i)
    path = [_index_to_node_time(i, len(dg.nodes)) for i in on_vars]
    path = [(e[0], list(dg.nodes)[e[1]]) for e in path]
    return path