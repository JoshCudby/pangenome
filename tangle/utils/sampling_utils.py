import numpy as np
import networkx as nx
from math import floor
from greedy import SteepestDescentSolver
from dimod.reference.samplers import SimulatedAnnealingSampler
from dimod import Sampler, BQM
from dwave.system import LeapHybridSampler


def dwave_sample_bqm(sampler: Sampler, bqm: BQM, time_limit=None, label="QUBO", num_reads=30):
    """Perform a batch of annealing with greedy post-processing on a given Binary Quadratic Model.

    Args:
        sampler (Sampler): The sampler to anneal with.
        bqm (BQM): The model to anneal.
        time_limit (int, optional): The time limit. Quantum solver only.
        label (str, optional): The label for sample submission on DWave platform. Quantum solver only.
        num_reads (int, optional): Number of runs in batch. Defaults to 30. Classical Solver only.
        
    Returns:
        (dict, float): Returns the best sample and best energy of the batch.
    """
    if isinstance(sampler, LeapHybridSampler):
        if time_limit == -1:
            time_limit = sampler.min_time_limit(bqm)
            print(f"Using default min time limit: {time_limit}")
        sampleset = sampler.sample(bqm, time_limit, label=label)
    elif isinstance(sampler, SimulatedAnnealingSampler):
        sampleset = sampler.sample(bqm, num_reads=num_reads)
    else:
        raise Exception("Unknown Sampler type")
    
    try:
        print(sampleset.info['timing'])
    except:
        pass
    
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
        print(path[(i + 1)*num_per_line:])
        
        
def validate_path(path: list, graph: nx.Graph):
    """Checks the constraints for a path on a graph.
    
    In particular:
     - does the path go along graph edges at each time step
     - is each node visited the correct number of times
     - is exactly one node visited per time step

    Args:
        path (list): _description_
        graph (nx.Graph): _description_
    """
    node_dict = {node: 0 for node in graph.nodes}
    node_dict['end'] = 0
    
    for i in range(len(path) - 1):
        v1 = path[i][1][0:-2]
        node_dict[v1] += 1
        v2 = path[i + 1][1][0:-2]
        if not (v1, v2) in graph.edges:
            if v1 =='end' and v2 == 'end':
                pass
            else:
                try:
                    start_value = graph.nodes[v1]["start"]
                    if not start_value == 'end' and v2 == 'end':
                        print(f'Broke graph edge at step {i}')
                except KeyError:
                    print(f'Broke graph edge at step {i}')
    
    for node in graph.nodes:
        missing_visits = graph.nodes[node]["normalised_weight"] - node_dict[node]
        if  missing_visits != 0:
            print(f'Did not meet node weight for node: {node}. Missing visits: {missing_visits}')
    
    time_offset = 0
    for i in range(len(path)):
        if i < path[i][0] + time_offset:
            print(f'Skipped time {i}')
            time_offset -= 1
        elif i > path[i][0] + time_offset:
            print(f'Visited 2 nodes at time {i}')
            
    for node in graph.nodes:
        try:
            if graph.nodes[node]["start"] == "start":
                if not path[0][1][0:-2] == node:
                    print(f'Did not start at Start node: {node}')
        except:
            pass
    
    if not path[-1][1] == 'end_0':
        print('Did not end at End node.')
            
    