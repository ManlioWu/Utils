import pandas as pd
import  json
import os.path as osp
from joblib import Parallel, delayed
import multiprocessing


def download_table(url):
    tables = pd.read_html(url)
    # print("table数量:",len(tables))
    if (len(tables) == 4):
        return tables[3]
    return None

def save_json(save_path, res):
    with open(save_path, 'w+') as out_file:
        json.dump(res, out_file, indent=2)
        out_file.close()


def crawl_one(url2, pdb_name):
    new_url = url2 + pdb_name
    try:
        pdb_info = download_table(new_url)
    except:
        return None
    
    if pdb_info is None:
        return
    temp = {}
    for _, chain_info in pdb_info.iterrows():
        chain_name = chain_info['Chain']
        cdr = chain_info['CDR']
        cluster = chain_info['Cluster']
        # key = f'{pdb_name.lower()}_{chain_name}_{cdr[0]}_cdr{cdr[1]}'
        key = f'{pdb_name.lower()}_{cdr[0]}_cdr{cdr[1]}'
        # print(key, cluster)
        if key not in temp:
            temp[key] = cluster
    return temp

def crawl():
    base_url = "http://dunbrack2.fccc.edu/PyIgClassify"
    url1 = osp.join(base_url, "Search/pdbs.aspx")
    url2 = osp.join(base_url, "Result/ChainCdrClusterInfo.aspx?pdb=")
    pdb_info = download_table(url1)
    pdb_names = pdb_info['PDB']
    parallel = Parallel(n_jobs=multiprocessing.cpu_count(), backend='multiprocessing',verbose=40)
    temp = parallel(delayed(crawl_one)(url2, pdb_name) for pdb_name in pdb_names)
    res = {}
    for d in temp:
        if d is not None:
            res.update(d)
    return res

if __name__ == '__main__':
    res = crawl()
    print(res)
    save_json('C://Users/manliowu/Desktop/cluster_info.json', res)
