import argparse
import os
import requests
import json
import ollama
import pandas as pd
from pathlib import Path 
from ast import literal_eval

def load_file_list (file):
    ''' Load list of LLM models to be evaluated into a python list. '''
    l = []
    j = open(file, "r")
    for line in j:
        l.append(line.rstrip())
    j.close()
    return l

def generate_bgp_config (url, models, prompt, local_as, remote_as, target, requirement, peer_df, long_context) :
    '''Send prompt to LLM deployed at a remote Ollama instance'''
    asns = local_as + remote_as

    ctx = generate_context([ i.strip('AS') for i in asns ], peer_df, "True")

    remote_as = ', '.join(remote_as)

    instruct = prompt.format(local_as=local_as[0], remote_as=remote_as)

    #context = f"{ctx}" 
    if long_context == "1":
        context = f"{ctx}" 
    else: 
        context = ""

   
    headers = {
        "Content-Type": "application/json"
    }

    prompt_text = f"{instruct} " + "Target device is " + f"{target}.\n" + f"{context}\n" + "Requirements:\n" + f"{requirement}\n\n  Answer:" 

    input = { 
        "model": f"{models}",
        "prompt": f"{prompt}",
        "instruct": f"{instruct}",
        "local_as": f"{local_as[0]}",
        "remote_as": f"{remote_as}",
        "target_device": f"{target}",
        "requirement": f"{requirement}",
        "long_context": f"{long_context}"
    }

    payload = {
        "model": models,
        "prompt": f"{prompt_text}",
        "system": """You are a helpful coding assistant expert at writing networking equipment configuration code.  Do not explain the code. Do not include comments.  Do not wrap code and output clean code only. Output Format: Return only the complete device configuration block — no commentary or explanation. /no_think /nothink""",
        "stream": False,
        "options": {"temperature": 0.5, "top_p": 0.9 } 
        }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    output = response.json()

    return input, payload, output


def concat_file_text (file_list): 

    file_content = ""
    
    for name in file_list: 
        with open(name) as infile: 
            file_content = file_content + infile.read()
    
    return file_content 


def generate_context ( peer_list, peer_df, ctx_full ): 

     netjson = { "bgp": {"peers":[], "local": {}}}
     local_as_dict = peer_df[peer_df['asn'] == peer_list[0]].to_dict('records')
     peer_dict = peer_df[peer_df['asn'].isin(peer_list[1:])].to_dict('records') 
     #p_string = [f"BGP Data:\nLocal AS: { local_as_dict[0]['asn'] }\n - Network Prefixes: { local_as_dict[0]['netpfx_ipv4']}\n "]
     netjson['bgp']['local']['asn'] = local_as_dict[0]['asn']
     netjson['bgp']['local']['routerID'] = local_as_dict[0]['peering_ip']
     netjson['bgp']['local']['network_prefixes'] = literal_eval(local_as_dict[0]['netpfx_ipv4'])

     if ctx_full == "True":

         for peer in peer_dict: 

              #p_string.append(f"Remote AS: { peer['asn'] } \n - Peering IP: {peer['peering_ip']} \n - Network Prefixes: {peer['netpfx_ipv4']} \n") 
              netjson['bgp']['peers'].append({ 'asn':peer['asn'], 'address':peer['peering_ip'], 'network_prefixes':literal_eval(peer['netpfx_ipv4']) }) 

     else: 

         for peer in peer_dict:

              #p_string.append(f"Remote AS: { peer['asn'] } \n - Peering IP: {peer['peering_ip']} \n")
              netjson['bgp']['peers'].append({ 'asn':peer['asn'], 'address':peer['peering_ip']})

     return json.dumps(netjson, indent=2)

# Function to append new data to JSON file
def write_json(new_data, filename='data.json'):

    file_path = filename

    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            file_data = {"results":[]}
            file_data["results"].append(new_data)
            json.dump(file_data, file, indent=4)
    else:
        with open(filename, 'r+') as file:
            file_data = json.load(file)
            file_data["results"].append(new_data)
            file.seek(0)
            json.dump(file_data, file, indent=4)


def main(): 

    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=str,
                    help="Enter the model name")
    parser.add_argument("outputdir", type=str,
                    help="specify output dir")
    parser.add_argument("long_context", type=str,
                    help="specify config type")
    parser.add_argument("url", type=str, help="specify ollama url")
    parser.add_argument("taskId", type=int, default=0, help="specify last task_id")
    args = parser.parse_args()

    # URL of the ollama instance
    url = 'http://10.153.60.46:11434/api/generate'
    # file path of the llm file list
    user_prompts = "data/bgp_prompts-10.txt"
    requirements = {'basic':"../requirements/01-basic.txt", 
                    'security':"../requirements/02-security.txt",
                    'performance':"../requirements/03-performance.txt", 
                   }
    target_devices = "data/target.txt"
    peer_df = pd.read_csv('/root/peeringllm.csv', index_col=0, low_memory=False)

    local_as = "AS9821"

    remote_as =["AS9299","AS4775","AS23862"]

    bgp_pair_df = pd.read_csv('data/bgp_pairs-3.csv',usecols=['ASN','peers_AS'], converters={"peers_AS": literal_eval})
    bgp_pair_list = bgp_pair_df.values.tolist()

    target_device = "JunOS (set command)"

    peer_df = pd.read_csv('/root/peeringllm.csv', index_col=0, low_memory=False)

    require = [ 
                concat_file_text([requirements['basic']]),
                concat_file_text([requirements['basic'],requirements['security']]),
                concat_file_text([requirements['basic'],requirements['performance']]),
                concat_file_text(requirements.values())
              ]
    require_idx = ["basic", "basic+security", "basic+performance", "basic+security+performance"]
    outputDir = args.outputdir
    model = args.model
    long_context = args.long_context
    url = args.url
    task_id = 0 
    taskId = args.taskId
    
    user_prompts = load_file_list(user_prompts)
    target_devices = load_file_list(target_devices) 

    for bgp_pairs in bgp_pair_list:
        ''' iterate over bgp pairs '''
        local_as = [f"{bgp_pairs[0]}"]
        for target_device in target_devices: 
            ''' iterate over target devices '''
            for idx, content in enumerate(require): 
                ''' iterate over requirements ''' 
                for prompts in user_prompts: 
                    ''' iterate over the user prompts ''' 
                    for n in range(0,9):
                        ''' iterate over the number of samples ''' 
                        input, payload, data = generate_bgp_config(url, model, prompts, local_as, bgp_pairs[1], target_device, content, peer_df, long_context)   
                        if n == 0:
                           print(input)
                           print(payload['prompt']) 
                        print(data['response']+'\n\n')
                        task_id += 1
                        write_json({"task_id":task_id,"requirements":require_idx[idx],"input":input,"payload":payload,"output":data}, filename=f"{outputDir}/{model}_{long_context}.txt")
                        


if __name__ == "__main__":
    main()
