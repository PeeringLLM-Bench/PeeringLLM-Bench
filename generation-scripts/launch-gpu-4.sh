#!/bin/bash 

while IFS="" read -r p || [ -n "$p" ]
do
  python generate.py "$p" ../output2 0 http://10.153.60.46:11444/api/generate
done < data/gpu-4.list
