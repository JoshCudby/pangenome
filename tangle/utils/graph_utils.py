import networkx as nx
import gfapy
from math import remainder
from scipy.optimize import minimize


def normalise_node_weights(graph: nx.Graph, normalisation: float):
    for node in graph.nodes:
        graph.nodes[node]["normalised_weight"] = round(graph.nodes[node]["weight"] / normalisation)
    return graph


def _coverage_cost_function(x, digraph):
    print(x)
    return sum((remainder(digraph.nodes[node]["weight"], x)) ** 2 for node in digraph.nodes)


def get_normalised_node_weights(graph: nx.Graph) -> tuple[nx.Graph, float]:
    total_node_weight = sum(graph.nodes[node]["weight"] for node in graph.nodes)
    average_node_weight = total_node_weight / len(graph.nodes)
    optimized_coverage = minimize(_coverage_cost_function, average_node_weight, graph, bounds=[(2, 1000)]).x[0]
    for node in graph.nodes:
        graph.nodes[node]["normalised_weight"] = round(graph.nodes[node]["weight"] / optimized_coverage)
    return graph, optimized_coverage


def digraph_from_gfa_file(filename) -> nx.DiGraph:
    gfa = gfapy.Gfa.from_file(filename)
    digraph = nx.DiGraph()
    for segment_line in gfa.segments:
        digraph.add_node(segment_line.name, sequence=segment_line.sequence, weight=segment_line.SC, start=segment_line.st)
    for edge_line in gfa.edges:
        digraph.add_edges_from([
            (edge_line.sid1.name, edge_line.sid2.name),
            (edge_line.sid2.name, edge_line.sid1.name),
        ])
    return digraph


def graph_from_gfa_file(filename: str) -> nx.Graph:
    gfa = gfapy.Gfa.from_file(filename)
    graph = nx.Graph()
    for segment_line in gfa.segments:
        graph.add_node(segment_line.name, sequence=segment_line.sequence, weight=segment_line.SC, start=segment_line.st)
    for edge_line in gfa.edges:
        graph.add_edges_from([
            (edge_line.sid1.name, edge_line.sid2.name)
        ])
    return graph


def toy_graph(exact_solution=True):
    weight_1 = 3 if exact_solution else 4
        
    g = nx.DiGraph()
    g.add_nodes_from([
        (0, {"weight": 1}),
        (1, {"weight": weight_1}),
        (2, {"weight": 1}),
        (3, {"weight": 1}),
        (4, {"weight": 1}),
    ])
    g.add_edges_from([
        (0, 1), (1, 2), (1, 3), (1, 4), (2, 1), (2, 3), (2, 4), (3, 1), (3, 2), (3, 4),
    ])
    return g
        

def setup_graph_for_tangle_qubo(graph, t_max):
    graph_copy = nx.DiGraph(graph)
    # Add virtual node to allow early finishes
    graph_copy.add_nodes_from(
        [("end", {"weight": t_max})],
    )    
    nodes = list(graph_copy.nodes)
    graph_copy.add_edges_from([
        (nodes[-1], nodes[-1]),
        (nodes[-2], nodes[-1])
    ])
    return graph_copy


def graph_to_max_path_digraph(graph: nx.Graph):
    dg = nx.DiGraph()
    for node in graph.nodes:
        weight = graph.nodes[node]["normalised_weight"]
        for k in range(weight):
            dg.add_node(f'{node}_{k}')
        
    for edge in graph.edges:
        if not edge[0] == edge[1]:
            weight_i = graph.nodes[edge[0]]["normalised_weight"]
            weight_j = graph.nodes[edge[1]]["normalised_weight"]
            for i in range(weight_i):
                for j in range(weight_j):
                    dg.add_edges_from([
                        (f'{edge[0]}_{i}', f'{edge[1]}_{j}'),
                        (f'{edge[1]}_{j}', f'{edge[0]}_{i}')
                    ])
        else:
            weight = graph.nodes[edge[0]]["normalised_weight"]
            for i in range(weight - 1):
                dg.add_edge(
                    f'{edge[0]}_{i}', f'{edge[0]}_{i + 1}'
                )
        
    dg.add_node('end')
    for node in graph.nodes:
        try:
            if graph.nodes[node]["start"] == "end":
                weight = graph.nodes[node]["normalised_weight"]
                for i in range(weight):
                    dg.add_edge(f'{node}_{i}', 'end')
                    dg.nodes[f'{node}_{i}']["start"] = "end"
            elif graph.nodes[node]["start"] == "start":
                weight = graph.nodes[node]["normalised_weight"]
                for i in range(weight):
                    dg.nodes[f'{node}_{i}']["start"] = "start"
        except:
            pass
    
    dg.add_edge('end', 'end')        
    
    return dg