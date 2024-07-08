import numpy as np
import sys
import subprocess
import re
import os
from datetime import datetime
from utils.sampling_utils import qubo_vars_to_path
from utils.graph_utils import graph_from_gfa_file, normalise_node_weights
from utils.qubo_utils import graph_to_max_path_digraph


if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    raise Exception('No MQLib file to read')

if len(sys.argv) > 2:
    try:
        normalisation = int(sys.argv[2])
    except ValueError:
        normalisation = 1
else:
    normalisation = 1

if len(sys.argv) > 3:
    try:
        time_limit = int(sys.argv[3])
    except ValueError:
        time_limit = 60
else:
    time_limit = 60

graph = graph_from_gfa_file(f"./data/{filename}")
graph = normalise_node_weights(graph, normalisation)
dg = graph_to_max_path_digraph(graph)

process = subprocess.run(["MQLib/bin/MQLib", "-fQ", f"./out/mqlib_input_{filename}.txt", "-h", "BURER2002", "-r", f"{time_limit}", "-ps"], capture_output=True)
out = process.stdout
out_str = out.decode("utf-8")
out_data = [x for x in out_str.split('\n') if len(x) > 0]
solution = out_data[2].split()
solution = [int(x) for x in solution]

W = len(dg.nodes) - 1
offset = W * (W + 3)
energy = int(out_data[0].split(',')[3])

path = qubo_vars_to_path(solution, dg)
save_dir = "out"
if not os.path.exists(save_dir):
    os.mkdir(save_dir)
    
now = datetime.now().strftime("%d%m%Y_%H%M")
save_file = save_dir + f"/qubo_mqlib_{now}"   
    
to_save = np.array([solution, offset - energy, path], dtype=object)
np.save(save_file, to_save)