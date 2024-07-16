#!/bin/bash

usage()
{
    echo "usage: compile_gurobi_data [[-k kmer]] | [-h]]"
}

get_path()
{
    awk -f bin/get_path.awk {}
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

## MAIN

out_dir="./out"
file_pattern="gurobi.*.$kmer.*.\d"
search_pattern="Best path"
stop_pattern="Energy of path"
max_lines=30

echo "Searching in dir: $out_dir"
# Find all files matching the file_pattern in the specified directory
files=$(find "$out_dir" -type f -name "$file_pattern")

# Iterate through each file and search for the pattern
for file in $files; do
    echo "Searching in file: $file"
    # Read the file line by line
    while IFS= read -r line; do
        # Check if the line matches the search pattern
        if echo "$line" | grep -q "$search_pattern"; then
            echo "$line"
            count=1
            # Continue reading lines until one matches the stop pattern
            while IFS= read -r next_line; do
                if echo "$next_line" | grep -q "$stop_pattern"; then
                    echo "$next_line"
                    break
                fi
                echo "$next_line"
                ((count++))
                if [ "$count" -ge "$max_lines" ]; then
                    break
                fi
            done
        fi
    done < "$file"
done