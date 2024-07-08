#!/bin/bash

usage()
{
    echo "usage: solver_benchmark [[[-f file ] [-n normalisation] [-t time limit] [-m memory]] | [-h]]"
}

# Defaults
memory=4000
time_limit=60
normalisation=1

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
        -m | --memory )         shift
                                memory="$1"
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
    echo "Reading file:" $filename
else
    echo "Could not find input file."
    exit 1
fi

case $normalisation in
    [0-9]* ) echo "Normalising node weights by:" $normalisation
             ;;
    *      ) echo "Normalisation was not a number."; exit 1
esac

case $time_limit in
    [0-9]* ) echo "Time limit:" $time_limit
             ;;
    *      ) echo "Time limit was not a number."; exit 1
esac

case $memory in
    [0-9]* ) echo "Memory:" $memory
             ;;
    *      ) echo "Memory was not a number."; exit 1
esac

## MAIN

# Gurobi solver
printf "\n\n"
echo "Gurobi Solver"
bsub -R '"select[mem>'$memory'] rusage[mem='$memory']"'  -M "$memory" -o "out/gurobi.$filename" -e "out/error.gurobi.$filename" -G "qpg" "python3 ./tangle/max_path_gurobi.py ./tangle/data/$filename $normalisation $time_limit"

# MQLib solver
printf "\n\n"
echo "MQLib Solver"
bsub -R '"select[mem>'$memory'] rusage[mem='$memory']"'  -M "$memory" -o "out/mqlib.$filename" -e "out/error.mqlib.$filename" -G "qpg" "python3 ./tangle/max_path_mqlib.py $filename $normalisation $time_limit"

# D-Wave solver
printf "\n\n"
echo "D-Wave Solver"
bsub -R "select[mem>1000] rusage[mem=1000]"  -M "1000" -o "out/dwave.$filename" -e "out/error.dwave.$filename" -G "qpg" "python3 ./tangle/max_path_qubo.py ./tangle/data/$filename $normalisation q"

exit 0