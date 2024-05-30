import networkx as nx
import gfapy


def digraph_from_file(filename):
    gfa = gfapy.Gfa.from_file(filename)
    digraph = nx.DiGraph()
    for segment_line in gfa.segments:
        digraph.add_node(segment_line.name, sequence=segment_line.sequence)
    for edge_line in gfa.edges:
        digraph.add_edges_from([
            (edge_line.sid1.name, edge_line.sid2.name),
            (edge_line.sid2.name, edge_line.sid1.name),
        ])
    return digraph


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
        

def setup_graph_for_qubo(graph, t_max):
    graph_copy = nx.DiGraph(graph)
    # Add virtual node to allow early finishes
    graph_copy.add_nodes_from(
        [(len(list(graph.nodes)), {"weight": t_max})],
    )    
    nodes = list(graph_copy.nodes)
    graph_copy.add_edges_from([
        (nodes[-1], nodes[-1]),
        (nodes[-2], nodes[-1])
    ])
    return graph_copy