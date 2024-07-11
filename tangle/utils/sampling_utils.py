import numpy as np
import networkx as nx
from math import floor
from greedy import SteepestDescentSolver
from dimod.reference.samplers import SimulatedAnnealingSampler
from dimod import Sampler, BQM
from dwave.system import LeapHybridSampler


def dwave_sample_bqm(sampler: Sampler, bqm: BQM, time_limit=None, num_reads=30, label="QUBO"):
    """Perform a batch of annealing on a given Binary Quadratic Model.

    Args:
        sampler (Sampler): The sampler to anneal with.
        bqm (BQM): The model to anneal.
        num_reads (int, optional): Number of runs in batch. Defaults to 30.

    Returns:
        (dict, float): Returns the best sample and best energy of the batch.
    """
    if isinstance(sampler, LeapHybridSampler):
        print(f"Minimum time limit: {sampler.min_time_limit(bqm)}")
        sampleset = sampler.sample(bqm, time_limit, label=label)
    elif isinstance(sampler, SimulatedAnnealingSampler):
        sampleset = sampler.sample(bqm, num_reads=num_reads)
    else:
        raise Exception("Unknown Sampler type")
    greedy_solver = SteepestDescentSolver()
    post_processed = greedy_solver.sample(bqm, initial_states=sampleset)
    
    best_sample = post_processed.first.sample
    best_energy = post_processed.first.energy
    return best_sample, best_energy


def get_path(sample: dict):
    """Deprecated"""
    return sorted([i for i in list(sample.keys()) if sample[i]], key=lambda e: e[1])


def get_node_visits(sample: dict):
    """Deprecated"""
    path = get_path(sample)
    nodes = set([key[0] for key in list(sample.keys())])
    node_visits = {node : 0 for node in nodes}
    for path_node in path:
        node_visits[path_node[0]] += 1
        
    return node_visits


def get_constraint_values(sample: dict, graph: nx.DiGraph):
    """Deprecated"""
    node_visits = get_node_visits(sample)
    constraint_values = np.array([node_visits[x] - graph.nodes.data()[x]["weight"] for x in list(graph.nodes)])
    return constraint_values


def _index_to_node_time(idx, num_nodes):
    """Converts a qubo index to a (time-step, node_index) pair

    Args:
        idx (int): index of qubo variable
        num_nodes (int): number of nodes in graph

    Returns:
        (int, int): A pair describing the corresponding path time-step and the node index
    """
    rem = idx % num_nodes
    div = floor(idx / num_nodes)
    return (div, rem)


def dwave_sample_to_path(sample: dict, dg: nx.DiGraph) -> list:
    """Gets the actual path as a list of (time, node) pairs from an output of a DWave Sampler.

    Args:
        sample (dict): the qubo variables as a dict.
        dg (nx.DiGraph): the directed graph underlying the problem.

    Returns:
        list: a list of (time_step, node) pairs.
    """
    on_vars = []
    for i in range(len(sample.keys())):
        if sample[i] == 1:
            on_vars.append(i)
    path = [_index_to_node_time(x, len(dg.nodes)) for x in on_vars]
    path = [(e[0], list(dg.nodes)[e[1]]) for e in path]
    return path


def qubo_vars_to_path(qubo_vars: list[int], dg: nx.DiGraph) -> list:
    """Gets the actual path as a list of (time, node) pairs from an array of qubo variable values.

    Args:
        qubo_vars (list[int]): the qubo variables as a list.
        dg (nx.DiGraph): the directed graph underlying the problem.

    Returns:
        list: a list of (time_step, node) pairs.
    """
    on_vars = []
    for i, var in enumerate(qubo_vars):
        if var == 1:
            on_vars.append(i)
    path = [_index_to_node_time(i, len(dg.nodes)) for i in on_vars]
    path = [(e[0], list(dg.nodes)[e[1]]) for e in path]
    return path


def print_path(path: list):
    """Pretty print a path"""
    num_per_line = 8
    for i in range(floor(len(path) / num_per_line)):
        print(path[i * num_per_line: (i + 1) * num_per_line])
    if not (i + 1) * num_per_line == len(path) - 1:
        print(path[(i + 1)*num_per_line:-1])