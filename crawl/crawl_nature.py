# use bs4
import argparse
from ast import parse
import multiprocessing
from joblib import Parallel, delayed
import pandas as pd
import requests
from bs4 import BeautifulSoup
import sys, threading
import time
sys.setrecursionlimit(10**7) # max depth of recursion
threading.stack_size(2**27)  # new thread will get stack of such size

# get pagesource
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

# key word
tar = ['artificial intelligence']
# types = ['Oral','Spotlight','Poster']


# crawl one paper
def crawl_one(paper):
    base_url = 'https://www.nature.com'

    # get paper title from tag <a> and its class 
    title_item = paper.find("a", class_="c-card__link u-link-inherit")
    title = title_item.text.strip('').strip('\n')
    url = title_item['href'].strip('').strip('\n')
    # get published time
    time = paper.find('time', class_='c-meta__item c-meta__item--block-at-lg').text.strip('').strip('\n')
    # get author list
    try:
        author_item = paper.find("ul", class_="c-author-list c-author-list--compact c-author-list--truncated")
        authors = []
        for author in author_item.find_all('li'):
            authors.append(author.text)
    except:
        pass


    # print(base_url+url)
    # print(title)
    # print(", ".join(authors))
    return {
        'Title' : f"[{title}]({base_url+url})",
        'Author(s)' : ",".join(authors).strip('').strip('\n'),
        'Published Date': time
    }
    

def crawl(keyword:str):
    keyword = keyword.replace('_', '+')
    base_url = f'https://www.nature.com/search?q={keyword}&journal=nature&article_type=research&date_range=1997-2023&order=date_desc'
    res = []

    soup = parse_url(base_url)
    pages_num = soup.find_all('a', class_="c-pagination__link")[-2].contents[-1].strip('').strip('\n')
    print(pages_num)

    # crawl each page
    for page_idx in range(int(pages_num)):
        # this page url
        soup1 = parse_url(base_url + f'&page={page_idx+1}')
        # find all papers in this page and crawl in parallel
        papers = soup1.find_all("li", class_="app-article-list-row__item")
        # print(papers)
        parallel = Parallel(n_jobs=multiprocessing.cpu_count(), backend='multiprocessing',verbose=40)
        temp = parallel(delayed(crawl_one)(paper) for paper in papers)

        # filter error items
        temp = list(filter(None, temp))
        res.extend(temp)

    df = pd.DataFrame(res)
    return df

# save as markdown file
def save_md(df, keyword):
    with open(f'./nature_{keyword}.md', 'w', encoding='utf8') as f:
        df.to_markdown(f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', type=str)
    args = parser.parse_args()

    # args.keyword= 'deep_learning'
    df = crawl(args.keyword)
    print(df)
    save_md(df, args.keyword)
    