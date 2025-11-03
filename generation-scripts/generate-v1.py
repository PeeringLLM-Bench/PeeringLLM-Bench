import argparse
import requests
import json
import ollama
import pandas as pd
from pathlib import Path 

def load_file_list (file):
    ''' Load list of LLM models to be evaluated into a python list. '''
    l = []
    j = open(file, "r")
    for line in j:
        l.append(line.rstrip())
    j.close()
    return l

def generate_bgp_config (url, models, user_prompts, local_as, remote_as, target, requirement, peer_df) :
    '''Send prompt to LLM deployed at a remote Ollama instance'''
    
    asns = [local_as] + remote_as

    ctx = generate_context([ i.strip('AS') for i in asns ], peer_df, False)

    remote_as = ', '.join(remote_as)

    instruct = prompt.format(local_as=local_as, remote_as=remote_as)

    context = f"{ctx}" 

    headers = {
        "Content-Type": "application/json"
    }

    prompt_text = f"{instruct} " + "Target device is " + f"{target}.\n" + f"{context}\n\n" + "Requirements:\n" + f"{requirement}" 

    payload = {
        "model": mx,
        "prompt": f"{prompt_text}",
        "system": """You are a helpful coding assistant expert at writing networking equipment configuration code. Assign peering IP address with /30 netmask.
                     Do not explain the code. Do not include comments.  Do not wrap code and output clean code only. /no_think""",
        "stream": False,
        "options": {"temperature": 0.2, "top_p": 0.9, "seed": 123} 
        }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    data = response.json()

    return payload, data 


def concat_file_text (file_list): 

    file_content = ""
    
    for name in file_list: 
        with open(name) as infile: 
            file_content = file_content + infile.read()
    
    return file_content 


def generate_context ( peer_list, peer_df, ctx_full ): 

     peer_dict = peer_df[peer_df['asn'].isin(peer_list)].to_dict('records') 

     if ctx_full == "True":

         p_string = [f"Data:\n\nOwn AS: { peer_dict[0]['asn'] }\n - Network Prefixes: { peer_dict[0]['netpfx_ipv4']}\n "]

         for peer in peer_dict[1:]: 

              p_string.append(f"AS Number: { peer['asn'] } \n - Peering IP: {peer['peering_ip']} \n - Network Prefixes: {peer['netpfx_ipv4']} \n") 

     else: 

         p_string = [f"Data:\n\nOwn AS: { peer_dict[0]['asn'] }\n - Network Prefixes: { peer_dict[0]['netpfx_ipv4']}\n "]

         for peer in peer_dict[1:]:

              p_string.append(f"AS Number: { peer['asn'] } \n - Peering IP: {peer['peering_ip']} \n")

     

     return '\n'.join(p_string)
                

#def generate_bgp_config_peer ()

       
    

def main(): 

    '''
    parser = argparse.ArgumentParser()
    parser.add_argument("name", type=str,
                    help="display the name")
    parser.add_argument("snapshot", type=str,
                    help="display snapshot dir")
    args = parser.parse_args()
    '''

    # URL of the ollama instance
    url = 'http://10.153.60.46:11434/api/generate'
    # file path of the llm file list
    coding_llm = "../coding-llms.txt"
    user_prompts = "../prompts/bgp_prompts.txt"
    requirements = {'basic':"../requirements/01-basic.txt", 
                    'security':"../requirements/02-security.txt",
                    'performance':"../requirements/03-performance.txt", 
                    'optimization':"../requirements/04-optimization.txt"}
    peer_df = pd.read_csv('/root/peeringllm.csv', index_col=0, low_memory=False)

    local_as = "AS9821"

    remote_as =["AS9299","AS4775","AS23862"]

    target_device = "JunOS"

    peer_df = pd.read_csv('/root/peeringllm.csv', index_col=0, low_memory=False)

    require = concat_file_text([requirements['basic']])
    
    requirements_content = require
    user_prompts = load_file_list(user_prompts)
    
    print(generate_bgp_config(url, qwen2.5-coder:32b, user_prompts[0], local_as, remote_as, target_device, requirements_content, peer_df))


if __name__ == "__main__":
    main()
