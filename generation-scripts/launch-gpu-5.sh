#!/bin/bash 

while IFS="" read -r p || [ -n "$p" ]
do
  python generate-ctx.py "$p" ../output-ctx 1 http://10.153.60.46:11445/api/generate 0 
done < data/gpu-5.list
