# use selenium
import argparse
from lib2to3.pgen2 import driver
import multiprocessing
from joblib import Parallel, delayed
import pandas as pd
import undetected_chromedriver as uc
import time
from selenium.webdriver.common.by import By

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc


# options = webdriver.ChromeOptions()
# # options.add_argument('--headless')
# options.add_argument("start-maximized")
# options.add_experimental_option("excludeSwitches", ["enable-automation"])
# options.add_experimental_option('useAutomationExtension', False)
# # options.add_argument(
# # 	'user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"')
# exe_path = '/path/to/chromedriver.exe'
# driver = webdriver.Chrome(executable_path=exe_path, options=options)    # Chrome浏览器

# # Open website
# driver.get("https://www.science.org/action/doSearch?AllField=Artificial+Intelligence&SeriesKey=science&startPage=&ConceptID=505154&AfterYear=1997&BeforeYear=2023&queryID=38%2F3168548807")

# time.sleep(10)
# temp = driver.page_source
# with open('./res.html', 'w+') as f:
#     f.write(temp)
#     f.close()
# print(temp)


def crawl_one_paper(paper):
    # get title and url from tag <a>
    paper_item = paper.find_element(By.CLASS_NAME, 'text-reset.animation-underline')
    title, url = paper_item.text, paper_item.get_attribute('href')
    
    # get the published time
    time = paper.find_element(By.TAG_NAME, 'time').text

    # get author list
    try:
        author_item = paper.find_elements(By.CLASS_NAME, "hlFld-ContribAuthor")
        authors = []
        for author in author_item:
            # if author is not None and len(author) > 0:
            authors.append(author.text)
        authors = ', '.join(authors)
    except Exception as e:
        print(e)
        authors = ''

    # return paper info
    return {
        'Title' : f"[{title}]({url})",
        'Author(s)' : authors,
        'Published Date': time
    }


def crawl_one_page(driver):
    # find all papers in this page, and crawl the information of each paper in parallel
    papers = driver.find_elements(By.CLASS_NAME, 'card.pb-3.mb-4.border-bottom')
    parallel = Parallel(n_jobs=multiprocessing.cpu_count(), backend='threading',verbose=40)
    page_res = parallel(delayed(crawl_one_paper)(paper) for paper in papers)

    return page_res


# get driver. timeout is used to bypass cloudflare. If no cloudflare, you can give it 0 
def init_driver(url, timeout=10):
    driver = uc.Chrome()
    driver.get(url)
    time.sleep(timeout)
    return driver


def crawl_all(keyword:str):
    # convert '_' to '+', because in url '+' is equal to space
    keyword = keyword.replace('_', '+')
    
    # website with some search parameters
    base_url = f'https://www.science.org/action/doSearch?AllField={keyword}&SeriesKey=science&ConceptID=505154&AfterYear=1997&BeforeYear=2023&queryID=38%2F3168548807&sortBy=Earliest'
    
    # get page number
    driver = init_driver(base_url)
    page_item = driver.find_elements(By.CLASS_NAME, 'page-item')
    page_num = len(page_item) - 2
    
    print('key_word: ', keyword)
    print('page num: ', page_num)

    res = []

    # crawl each page
    for page_idx in range(page_num):
        print(f'Now is crawling page {page_idx+1}/{page_num}')
        page_res = crawl_one_page(driver)
        res.extend(page_res)

        # next page
        driver.find_element(By.CLASS_NAME, 'page-item__arrow--next').click()
        
    df = pd.DataFrame(res)

    # end crawl, close the opened browser
    driver.quit()
    return df


# save as markdown file
def save_md(df, keyword):
    with open(f'./science_{keyword}.md', 'w', encoding='utf8') as f:
        df.to_markdown(f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # replacing 'space' with '_', because parser cannot handle the word with space
    parser.add_argument('--keyword', type=str)
    args = parser.parse_args()

    df = crawl_all(args.keyword)
    print(df)
    save_md(df, args.keyword)

