import pandas as pd 

peer_df = pd.read_csv('/root/peeringllm.csv', index_col=0, low_memory=False)

etl_df_sorted_ren[['asn','class']].groupby("class").sample(frac=0.01, random_state=1)
