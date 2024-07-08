#!/bin/bash

usage()
{
    echo "usage: solver_benchmark [[[-f file ] [-n normalisation]] | [-h]]"
}

while [ "$1" != "" ]; do
    case $1 in
        -f | --file )           shift
                                filename="$1"
                                ;;
        -n | --normalisation )  shift
                                normalisation="$1"
                                ;;
        -t | --time )           shift
                                time_limit="$1"
                                ;;
        -h | --help )           usage
                                exit
                                ;;
        * )                     usage
                                exit 1
    esac
    shift
done

if [ -f "./tangle/data/"$filename ]; then
    echo "Reading file:"; echo $filename
else
    echo "Could not find input file."
    exit 1
fi

case $normalisation in
    [0-9]* ) echo "Normalising node weights by:"; echo $normalisation
             ;;
    *      ) echo "Normalisation was not a number."; exit 1
esac

# Gurobi solver
printf "\n\n"
echo "Gurobi Solver"
python3 "./tangle/max_path_gurobi.py" "./tangle/data/"$filename $normalisation $time_limit

# MQLib solver
printf "\n\n"
echo "MQLib Solver"
python3 "./tangle/max_path_mqlib.py" $filename $normalisation $time_limit

# D-Wave solver
printf "\n\n"
echo "D-Wave Solver"
python3 "./tangle/max_path_dwave.py" "./tangle/data/"$filename $normalisation q

exit 0