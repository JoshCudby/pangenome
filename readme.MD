# Installation

Run `https://github.com/JoshCudby/pangenome.git --recurse-submodules` to clone with the submodules.

If you have already run `git clone` without `--recurse-submodules`, you can instead use `git submodule update --init --recursive`.

Packages:
- numpy
- dwave-ocean-sdk
- gfapy
- gurobipy
- networkx

See `environment.yml`.

To use the Gurobi solver, you will need to obtain a licence. Instructions available at https://support.gurobi.com/hc/en-us/articles/14799677517585-Getting-Started-with-Gurobi-Optimizer .

To use the D-Wave hybrid solver, you will need an API key and a configuration file. Your API key can be found on the Leap Dashboard once you have made an account: https://cloud.dwavesys.com/leap/ . The configuration file can be made using the CLI tool as discussed here: https://docs.ocean.dwavesys.com/en/stable/docs_cli.html#dwave-cli . 

# Usage

The current main scripts are `max_path_qubo.py` and `max_path_gurobi.py`.
They are currently set up to accept `.gfa` files with `ec` tags representing the coverage of each node.

`max_path_qubo` uses D-Wave's hybrid or classical solvers. `max_path_gurobi` uses the SOTA Gurobi optimisation tool.

Example usage for the qubo variant is `python max_path_qubo.py data/ddDapMeze1.mito.gfa 250 q` where the arguments are:
- file path
- coverage normalisation factor
- `q` for hybrid quantum-classical solver or `c` for classical solver.

Example usage for the Gurobi variant is `python max_path_gurobi.py data/ddDapMeze1.mito.gfa 250 q` where the arguments are:
- file path
- coverage normalisation factor

