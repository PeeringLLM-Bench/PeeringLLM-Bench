#!/bin/bash 

while IFS="" read -r p || [ -n "$p" ]
do
  python generate-ctx-v2.py "$p" ../output-ctx 1 http://10.153.60.45:11434/api/generate 0
done < data/gpu-0.list
