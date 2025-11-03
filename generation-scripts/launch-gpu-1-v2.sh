#!/bin/bash 

while IFS="" read -r p || [ -n "$p" ]
do
  python generate-ctx-v2.py "$p" ../output-candar 1 http://10.153.60.46:11443/api/generate 0
done < candar-peering-llm2/data/gpu-candar-list-1.txt
