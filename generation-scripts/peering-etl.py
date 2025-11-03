import pandas as pd 
import ipaddress

def expand_pfx (x): 
    ntwrk = x[0]
    pfx = x[1]
    asn = x[2].split('_')
    return "%s/%s" % (ntwrk,pfx), asn
        
# create dataframe 
df = pd.read_table("data/routeviews-rv2-20250517-1000.pfx2as", delimiter="\t", names=['network','prefix','as'])

expand_df = df.apply(lambda x: expand_pfx(x.values), axis=1, result_type='expand')

explode_df = expand_df.explode(1)
etl_df = explode_df.groupby(1)[0].apply(list).reset_index()

etl_df_sorted = etl_df

etl_df_sorted['netpfx_ipv4'] = etl_df_sorted[0].apply(lambda x: [ipaddress.IPv4Network(i) for i in x]).apply(lambda x: [format(i) for i in ipaddress.collapse_addresses(x)])
etl_df_sorted['peering_net'] = etl_df_sorted['netpfx_ipv4'].apply(lambda x: x[0])
etl_df_sorted['peering_ip'] = etl_df_sorted['peering_net'].apply(lambda x: format(ipaddress.IPv4Network(x)[0]+1))
etl_df_sorted['remote_ip'] = etl_df_sorted['peering_net'].apply(lambda x: format(ipaddress.IPv4Network(x)[0]+2))
etl_df_sorted_ren = etl_df_sorted.rename(columns={1:"asn",0:"netpfx"})
etl_df_sorted_ren['numPfx'] = etl_df_sorted_ren[['netpfx_ipv4']].apply(lambda x: len(x.values[0]), axis=1)
etl_df_sorted_ren['cumSumPfx'] = etl_df_sorted_ren['numPfx'].cumsum()
etl_df_sorted_ren.to_csv('peeringllm.csv')
print(etl_df_sorted_ren)
