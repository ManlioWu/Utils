# using bs4. Crawl ICLR、ICML、Neurips parameterized with keywords and published year
import argparse
import multiprocessing
from joblib import Parallel, delayed
import pandas as pd
import requests
from bs4 import BeautifulSoup
import sys, threading
import time
sys.setrecursionlimit(10**7) # max depth of recursion
threading.stack_size(2**27)  # new thread will get stack of such size

def parse_url(url):
    page = None
    while page is None:
        try:
            page = requests.get(url, stream=True)
            break
        except:
            time.sleep(2)

    soup = BeautifulSoup(page.content, "html.parser")
    return soup

# keywords
tar = ['equivariant', 'equivarience', 'invariant', 'invariance', 'steerable']
# article type(rating)
types = ['Oral','Spotlight','Poster']

def crawl_one(base_url, paper, tp):
    idx = paper['id'].split('_')[-1]
    paper_url = base_url + f'?showEvent={idx}'
    soup = parse_url(paper_url)
    # get abstract
    abstract = soup.find("div", class_="abstractContainer").text
    title = paper.find("div", class_="maincardBody").text
    author = paper.find("div", class_="maincardFooter").text.replace(' · ',',')

    # search key words
    if 'graph' in abstract.lower():
        for k in tar:
            if k in title.lower() or k in abstract.lower():
                return {
                    'Title' : f"[{title}]({paper_url})",
                    'Author(s)' : author,
                    'Decision': tp
                }
    return None
    

def crawl(conf, year):
    base_url = f'https://{conf}.cc/Conferences/{year}/Schedule'
    res = []
    for tp in types:
        soup1 = parse_url(base_url + f'?type={tp}')
        papers = soup1.find_all("div", class_="maincard narrower " + tp.lower())
        parallel = Parallel(n_jobs=multiprocessing.cpu_count(), backend='multiprocessing',verbose=40)
        temp = parallel(delayed(crawl_one)(base_url, paper, tp) for paper in papers)
        temp = list(filter(None, temp))
        res.extend(temp)

    df = pd.DataFrame(res)
    return df


def save_md(df, conf, year):
    with open(f'{conf}_{year}_equivariant.md', 'w', encoding='utf8') as f:
        df.to_markdown(f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--conf', type=str, required=True)
    parser.add_argument('--year', type=int, required=True)
    args = parser.parse_args()

    conf, year = args.conf, args.year
    df = crawl(conf, year)
    print(df)
    save_md(df, conf, year)
    