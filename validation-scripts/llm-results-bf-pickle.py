#!/bin/python

import argparse
import pandas as pd
import tempfile
import os
import json
from pybatfish.client.session import Session
from pybatfish.datamodel import *
from pybatfish.datamodel.answer import *
from pybatfish.datamodel.flow import *
from ast import literal_eval
import itertools
import numpy as np
import re

pd.set_option('display.max_columns', None)

def stripComments(code):
    code = str(code)
    return re.sub(r'(?m)^ *!.*\n?', '', code)

def calc_defect_density(config, bf_parse_stat):
    if bf_parse_stat[0]:
        return len(bf_parse_stat[0]) / len(config.splitlines())
    else:
        return int(0)

def estimate_pass_at_k(num_correct, num_samples=100, k=1):
    """Estimates pass@k of each problem and returns them in an array."""
    
    def estimator(n: int, c: int, k: int) -> float:
        """Calculates 1 - comb(n - c, k) / comb(n, k)."""
        if n - c < k:
            return 1.0
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

    if isinstance(num_samples, int):
        num_samples_it = itertools.repeat(num_samples, len(num_correct))
    else:
        assert len(num_samples) == len(num_correct)
        num_samples_it = iter(num_samples)
    return estimator(int(num_samples), num_correct.sum(),k)

def return_bf_results (batfish_host, config, local_as, remote_peers, task_id, model, long_context, peer_df):

    mod = model.replace(":","_")
    session_name = f"network{task_id}"
    remote_peers = [x.lstrip('AS') for x in remote_peers.split(',')]
    local_as_dict = peer_df[peer_df['asn'] == local_as.lstrip('AS')].to_dict('records')
    peer_dict = peer_df[peer_df['asn'].isin(remote_peers)].to_dict('records')        

    with tempfile.TemporaryDirectory() as tmpdirname:
        
        # config path
        config_path = tmpdirname + '/configs'
        batfish_path = tmpdirname

        # Create config directory
        os.mkdir(config_path)
        
        # generate peer configuration file 
        if long_context == "1":
            for peer in peer_dict:
                config_bgp = f"""
hostname as{peer['asn']}
interface GigabitEthernet0/1
  ip address {peer['peering_ip']} 255.255.255.252\nrouter bgp {peer['asn']}
  network {literal_eval(peer['netpfx_ipv4'])[0]}
  neighbor {peer['peering_ip'][:-1]}2 remote-as {local_as_dict[0]['asn']}
ip route {literal_eval(peer['netpfx_ipv4'])[0]} null0
                """
                #print(config_bgp)
                with open(config_path + f"/as{peer['asn']}.cfg", "w+") as text_file:
                    text_file.write(config_bgp)
        #print(config)
        # Write config into file 
        with open(config_path + "/peeringllm.cfg", "w+") as text_file:
            text_file.write(config)
        #print(os.listdir(config_path))    
        # initialize batfish  
        bf = Session(host=batfish_host) 
        bf.set_network(session_name)
        bf.init_snapshot(batfish_path, name=session_name, overwrite=True)
        
        # invoke query 
        resultinitIssues = bf.q.initIssues().answer().frame()
        resultfileParseStatus = bf.q.fileParseStatus().answer().frame()
        resultparseWarning = bf.q.parseWarning().answer().frame()
        resultbgpSession = bf.q.bgpSessionCompatibility().answer().frame()

        return [resultinitIssues.to_dict('records'), 
                resultfileParseStatus.to_dict('records'),
                resultparseWarning.to_dict('records'),
                resultbgpSession.to_dict('records')]

def valid_config (config, target):
    
    # Search for code block
    match = re.findall(r"^```(?s:.*?)```", config, re.M)
    # Check if a match is found and extract the code
    if match:
        config = match[0].strip('```')
    # Remove empty lines from code
    config = os.linesep.join([s for s in config.splitlines() if s])
    # Remove comment lines from code
    #config = stripComments(config)
    
    if target == 'Cisco IOS':
        header = '!RANCID-CONTENT-TYPE: cisco \n'
    elif target == 'Cisco IOS-XR':
        header = '!RANCID-CONTENT-TYPE: cisco-xr \n'
    elif target == 'Cisco NX-OS':
        header = '!RANCID-CONTENT-TYPE: cisco-nx \n'
    elif target == 'Juniper JunOS (set)':
        header = '!RANCID-CONTENT-TYPE: junos \n'
    elif target == 'Free-Range Routing (FRR)': 
        header = f'peeringllm\n# This file describes the network interfaces\n# ports.conf --\nfrr version\n'
    elif target == 'Arista EOS':
        header = '!RANCID-CONTENT-TYPE: arista \n'
    return f"{header} {config}"

def return_bgp_status (bfStatuslist, config_status, long_context):
    if bfStatuslist and (config_status == 1): 
        if long_context == "1":
            bgp_true = "UNIQUE_MATCH"
            if bgp_true in [item['Configured_Status'] for item in bfStatuslist if item['Node'] == "peeringllm"]:
                return 1
            else : return 0
        else: 
            bgp_true = "UNKNOWN_REMOTE"
            if bfStatuslist[-1]['Configured_Status'] == bgp_true: return 1 
            else: return 0 
    else: return 0

parser = argparse.ArgumentParser()
parser.add_argument("inputfile", type=str,
               help="Enter the model name")
parser.add_argument("outputfile", type=str,
               help="specify output dir")
args = parser.parse_args()

inputFile = args.inputfile
outputFile = args.outputfile

with open(inputFile) as f:
    data = json.load(f)
# Use pd.json_normalize to convert the JSON to a DataFrame
df = pd.json_normalize(data['results'])
peer_df = pd.read_csv('/root/peeringllm.csv', index_col=0, low_memory=False)
# get smaller df 
#df_s = df.head(100)
df_s = df
df_s['formatted_config'] = df_s.apply(lambda x: valid_config(x['output.response'], x['input.target_device']), axis=1) 
df_s['bfStatus'] = df_s.apply(lambda x: return_bf_results('10.158.98.15', 
                                                                x['formatted_config'], 
                                                                x['input.local_as'],
                                                                x['input.remote_as'],
                                                                x['task_id'], 
                                                               x['input.model'],
                                                                x['input.long_context'],
                                                                peer_df), axis=1)    
df_s['config_score'] = df_s.apply(lambda x: 1 if x['bfStatus'][1][-1]['Status'] == "PASSED" else 0, axis=1)
df_s['bgp_score'] = df_s.apply(lambda x: return_bgp_status( x['bfStatus'][3], x['config_score'], x['input.long_context'] ), axis=1)
df_s['defect_density_score'] = df_s.apply(lambda x: calc_defect_density( x['formatted_config'], x['bfStatus']), axis=1)
df_s.to_pickle(outputFile)
