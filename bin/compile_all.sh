#!/bin/bash

usage()
{
    echo "usage: compile_all [[-k kmer]] | [-h]]"
}

while [ "$1" != "" ]; do
    case $1 in
        -k | --kmer )   shift
                        kmer="$1"
                        ;;
        -h | --help )   usage
                        exit
                        ;;
        * )             usage
                        exit 1
    esac
    shift
done

for solver in dwave gurobi mqlib
do
    bin/compile_data.sh -s $solver -k $kmer
done