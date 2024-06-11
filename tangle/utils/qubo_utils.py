import networkx as nx
import numpy as np
from itertools import product
from dimod.reference.samplers import SimulatedAnnealingSampler
from dimod import Sampler, BQM
from dwave.system import LeapHybridSampler
from utils.graph_utils import setup_graph_for_tangle_qubo, graph_to_max_path_digraph
from utils.sampling_utils import get_constraint_values, get_path, get_max_path_problem_path_from_sample


def _max_path_problem_qubo_matrix(graph: nx.DiGraph, penalty) -> np.ndarray:
    nodes = list(graph.nodes)
    end_node = nodes[-1]
    W = len(nodes) - 1
    
    qubo_matrix = np.zeros(shape=(W+1, W+1, W+1, W+1), dtype=int)
    for t in range(W):
        for i, j in product(range(W+1), range(W+1)):
            if (nodes[i], nodes[j]) not in graph.edges:
                qubo_matrix[t, i, t+1, j] += penalty
            else:
                qubo_matrix[t, i, t+1, j] += -1 if (nodes[i] != end_node and nodes[j] != end_node) else 0
    
    for t in range(W+1):
        for i in range(W+1):
            qubo_matrix[t, i, t, i] -= penalty
            for j in range(i+1, W+1):
                qubo_matrix[t, i, t, j] += 2 * penalty
                
    for i in range(W):
        for t1 in range(W+1):
            for t2 in range(t1+1, W+1):
                qubo_matrix[t1, i, t2, i] += penalty
    
    qubo_matrix[1, 1, 1, 1] -= penalty
    qubo_matrix[W, W, W, W] -= penalty
    
    qubo_matrix = qubo_matrix.reshape(((W+1)**2, (W+1)**2))
    
    return qubo_matrix


def _tangle_problem_bqm(graph: nx.Graph, lamda: list, mu: float, P: int) -> BQM:
    """Returns a Binary Quadratic Model for the tangle problem.
    
    The tangle problem is to find the longest path through a node-weighted graph, where any node can be visited at most its weight many times.

    Args:
        graph (nx.Graph): the node-weighted graph which underlies the tangle problem
    """
    bqm = BQM({}, {}, 0, "BINARY")
    t_max = sum(graph.nodes.data()[node]["weight"] for node in graph.nodes) + 1
    
    qubo_graph = setup_graph_for_tangle_qubo(graph, t_max)
    nodes = list(qubo_graph.nodes)
    edges = list(qubo_graph.edges)
    
    # Reward travelling along true edges; penalise travelling not along edges
    for t in range(t_max - 1):
        for i, j in product(range(len(nodes)), range(len(nodes))):
            bqm.add_interaction(
                (nodes[i], t), 
                (nodes[j], t + 1), 
                -1 if ((nodes[i], nodes[j]) in edges) else P
            )
                
        # Travelling the virtual edges should not be rewarded
        bqm.add_interaction((nodes[-2], t), (nodes[-1], t + 1), 1)
        bqm.add_interaction((nodes[-1], t), (nodes[-1], t + 1), 1)
    
    # Penalise not starting at start or ending at end
    bqm.add_linear((nodes[0], 0), -P)
    bqm.add_linear((nodes[-1], t_max - 1), -P)
    bqm.offset += 2 * P
    
    # Penalise multiple locations at one time
    for t in range(t_max):
        bqm.offset += P
        for i in range(len(nodes)): 
            bqm.add_linear((nodes[i], t), -P)
            for j in range(i):
                bqm.add_interaction((nodes[i], t), (nodes[j], t), 2 * P) 
                
    # Generalised Lagrangian Penalties
    for i in range(len(nodes) - 1):
        weight = qubo_graph.nodes.data()[nodes[i]]["weight"]
        bqm.offset += mu / 2 * weight ** 2 - lamda[i] * weight
        for t1 in range(t_max):
            bqm.add_linear((nodes[i], t1), mu / 2 * (1 - 2 * weight) + lamda[i])
            for t2 in range(t1):
                bqm.add_interaction((nodes[i], t2), (nodes[i], t1), mu)
    
    return bqm
    

def _sample_bqm(sampler: Sampler, bqm: BQM, num_reads=30, label="QUBO"):
    """Perform a batch of annealing on a given Binary Quadratic Model.

    Args:
        sampler (Sampler): The sampler to anneal with.
        bqm (BQM): The model to anneal.
        num_reads (int, optional): Number of runs in batch. Defaults to 30.

    Returns:
        (dict, float): Returns the best sample and best energy of the batch.
    """
    if isinstance(sampler, LeapHybridSampler):
        sampleset = sampler.sample(bqm, time_limit=6, label=label)
    elif isinstance(sampler, SimulatedAnnealingSampler):
        sampleset = sampler.sample(bqm, num_reads=num_reads)
    else:
        raise Exception("Unknown Sampler type")
    best_sample = sampleset.first.sample
    best_energy = sampleset.first.energy
    return best_sample, best_energy


def _tangle_problem_iteration(sampler: Sampler, graph: nx.DiGraph, lamda: list, mu: float, P: int):
    """Perform one iteration of the tangle problem using the generalised Lagrangian method.

    Args:
        sampler (Sampler): The classical or quantum sampler to perform the annealing.
        graph (nx.DiGraph): The node-weighted graph which underlies the problem.
        lamda (list): The linear generalised Lagrangian variables.
        mu (float): The quadratic generalised Lagrangian variable.
        P (int): The penalty for traversing non-edges.

    Returns:
        (dict, float, list): Returns the best solution, best energy and list of node-weight constraint values.
    """
    bqm = _tangle_problem_bqm(graph, lamda, mu, P)
    best_sample, best_energy = _sample_bqm(sampler, bqm)
    constraint_values = get_constraint_values(best_sample, graph)
    return best_sample, best_energy, constraint_values


def tangle_problem(graph: nx.DiGraph, sampler=None, lamda=None, mu=0.5, growth_factor=1.1, P=10):
    """Solve the tangle problem using the generalised Lagrangian method.

    Args:
        graph (nx.DiGraph): node-weighted graph underlying the tangle problem.
        sampler (Sampler, optional): The sampler to use. Defaults to None.
        lamda (np.ndarray, optional): Initial values for the linear Lagrangian variables. Defaults to None.
        mu (float, optional): Initial value for the quadratic Lagrangian variable. Defaults to 0.5.
        growth factor (float, optional): Growth rate for quadratic Lagrangian variable after each iteration. Defaults to 1.1.
        P (int, optional): The penalty for traversing non-edges. Defaults to 10.

    Returns:
        (dict, float64, list, float): Returns the best variable assignment and the corresponding energy as well as the lagrangian variable values.
    """
    if sampler is None:
        sampler = SimulatedAnnealingSampler()
    if lamda is None:
        lamda = np.array([0] * len(list(graph.nodes)), dtype=float)
        
    if not all("weight" in x[1].keys() for x in graph.nodes.data()):
        raise Exception("Graph is not node-weighted")
    if not len(lamda) == len(list(graph.nodes)):
        raise Exception("Require one linear Lagrangian variable per graph node")
    if mu <= 0:
        raise Exception("Quadratic Lagrangian variable should be strictly positive")
    if growth_factor <= 1:
        raise Exception("Growth factor should be strictly greater than 1")
        
    best_sample, best_energy, constraint_values = _tangle_problem_iteration(sampler, graph, lamda, mu, P)
    print(f'Best path={get_path(best_sample)}\nBest energy={best_energy}\nConstraint values={list(zip(graph.nodes, constraint_values))}\n')
    while not all(constraint_values <= 0):
        lamda += (constraint_values > 0) * mu * constraint_values
        mu *= growth_factor
        
        best_sample, best_energy, constraint_values = _tangle_problem_iteration(sampler, graph, lamda, mu, P)
        print(f'Best path={get_path(best_sample)}\nBest energy={best_energy}\nConstraint values={list(zip(graph.nodes, constraint_values))}\n')

    return best_sample, best_energy, lamda, mu


def max_path_problem(graph: nx.Graph, sampler=None, penalty=None):
    """Solves the max path problem on a node-weighted graph.

    Args:
        graph (nx.Graph): The underlying graph.
        sampler (Sampler, optional): The sampler to use. Defaults to SimulatedAnnealingSampler.
        penalty (int, optional): The penalty for breaking constraints. Defaults to total weight of graph.
    """
    if sampler is None:
        sampler = SimulatedAnnealingSampler()
    
    dg = graph_to_max_path_digraph(graph)
    W = len(dg.nodes) - 1
    
    if penalty is None:
        penalty = W
    
    qubo_matrix = _max_path_problem_qubo_matrix(dg, penalty)
    bqm = BQM(qubo_matrix, 'BINARY')
    bqm.offset = penalty * (2*W + 4)
    
    best_sample, best_energy = _sample_bqm(sampler, bqm, label="Max Path QUBO")
    
    best_path = get_max_path_problem_path_from_sample(best_sample, dg)
    return best_sample, best_energy, best_path