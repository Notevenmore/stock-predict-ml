from bs4 import Tag

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import pandas as pd

import json
import os

from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from threading import RLock

from config import config, Browser
from helper import matching, element_to_formatted_text
from database import StockDB
from flask import current_app as app

tqdm.set_lock(RLock())

class NewsRepository:
    max_retries = 3
    EXECUTE_SCRIPT = "window.scrollTo(0, document.body.scrollHeight);"

    def __init__(self, is_init=False):
        self.news_category = json.loads(os.getenv("CATEGORY"))
            
        self.media_url = json.loads(os.getenv("MEDIA_URL"))
        self.months = json.loads(os.getenv("MONTHS"))
        self.news = {}
        self.newest_date = {}

        if is_init:
            self.load_news_data()
    
    def get_news(self, stock_name, page, limit):
        if self.news is None:
            return []
        
        if self.news[stock_name] is None:
            return []
        
        start = (page - 1) * limit
        end = start + limit
        result = self.news[stock_name].iloc[start:end]
        
        return result
    
    def load_news_data(self):
        with app.app_context():
            stocks = [
                stock.code for stock in StockDB.query.all()
            ]

        if len(stocks) == 0:
            self.news = None
            self.newest_date = None
        else:
            for stock in stocks:
                try:
                    self.news[stock] = pd.read_csv(f'data/News/{stock}.csv')
                    if 'Unnamed: 0' in self.news[stock].columns:
                        self.news[stock].drop('Unnamed: 0', axis=1, inplace=True)
                except FileNotFoundError:
                    self.news[stock] = None
                    self.newest_date[stock] = datetime.strptime(config.start, "%Y-%m-%d")
    
    def update_news_data(self):
        with app.app_context():
            stocks = [
                stock.code for stock in StockDB.query.all()
            ]

        for stock in stocks:
            if self.news[stock] is not None:
                if 'date' in self.news[stock].columns:
                    self.newest_date[stock] = self.news[stock]['date'].max()

                    if pd.isna(self.newest_date[stock]):
                        self.newest_date[stock] = datetime.strptime(config.start, "%Y-%m-%d")
                    else:
                        self.newest_date[stock] = datetime.strptime(self.newest_date[stock], "%Y-%m-%d")    
                else:
                    self.newest_date[stock] = datetime.strptime(config.start, "%Y-%m-%d")
            else:
                self.newest_date[stock] = datetime.strptime(config.start, "%Y-%m-%d")

            self.scrape_and_save_news(stock)
    
    def scrape_and_save_news(self, stock_name):
        new_news_list = []
        position = 0
        company_pattern = self.load_company_pattern()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            futures.append(executor.submit(self.load_detik_news, stock_name, position, company_pattern))
            position += 2
            
            futures.append(executor.submit(self.load_cnn_indonesia_news, stock_name, position, company_pattern))
            position += 2

            futures.append(executor.submit(self.load_idx_news, stock_name, position, company_pattern))
            position += 2

            for category in self.news_category["bisnis"]:
                futures.append(executor.submit(self.load_bisnis_com, category, stock_name, position, company_pattern))
                position += 2

            for category in self.news_category["tribunnews"]:
                futures.append(executor.submit(self.load_tribun_news, category, stock_name, position, company_pattern))
                position += 2

            for f in as_completed(futures):
                new_news_list.extend(f.result())
            
        new_news_list = sorted(new_news_list, key=lambda x: x['date'])
        new_news_list = pd.DataFrame(new_news_list)
        if self.news[stock_name] is None:
            self.news[stock_name] = new_news_list
        else:
            self.news[stock_name] = pd.concat([self.news[stock_name], new_news_list], ignore_index=True)

        if "link" in self.news[stock_name].columns:
            self.news[stock_name].drop('link', axis=1, inplace=True)

        self.news[stock_name].fillna('', inplace=True)
        self.news[stock_name].drop_duplicates(subset=['title'], keep='first', inplace=True)
        self.news[stock_name].to_csv(f"data/News/{stock_name}.csv")
    
    def load_company_pattern(self):
        with app.app_context():
            stocks = StockDB.query.all()
    
        stock_categories = {stock.code: stock.categories for stock in stocks}
        stocks = [
            stock.code for stock in stocks
        ]

        company_international_keys = {
            stock: {stock} | set(stock_categories[stock])
            for stock in stocks
        }

        company_international_key_lower = {
            stock: [
                company_international_key.lower() for company_international_key in company_international_keys[stock]
            ]
            for stock in stocks
        }

        company_pattern = {
            stock: config.build_pattern(company_international_key_lower[stock]) 
            for stock in stocks
        }

        return company_pattern

    def append_new_news(self, news, link, publish_date, text, stock_name, company_pattern):

        publish_date_datetime_format = datetime.strptime(publish_date, "%Y-%m-%d")
        start_date = datetime.strptime(config.start, "%Y-%m-%d")
        
        if self.break_condition(stock_name, text, publish_date_datetime_format):
            return True
        
        if publish_date_datetime_format < start_date:
            return True

        if not text or text in [n['title'] for n in news]:
            return False

        if not link:
            return False
        
        if(config.national_pattern.search(text) or config.international_pattern.search(text) or company_pattern[stock_name].search(text)):
            news.append({
                "link": link,
                "title": text,
                "date": publish_date,
                "content": ""
            })
        
        return False
    
    def break_condition(self, stock_name, text, publish_date_datetime_format):
        if self.news[stock_name] is not None:
            if text in self.news[stock_name]["title"]:
                return True

        if self.newest_date[stock_name] is not None:
            if publish_date_datetime_format < self.newest_date[stock_name]:
                return True
        
        return False
    
    def get_paginate_based_on_biggest_number_element(self, paginations):
        total_page = 1
        for pagination in paginations:
            text = pagination.text.strip()
            try:
                page = int(text)
                if total_page < page:
                    total_page = page
            except ValueError:
                continue
        return total_page
    
    def fetch_news_article(self, contents, news, filled_condition):
        for content in contents:
            if filled_condition == 'empty_class':
                if content.get("class"):
                    continue
            elif filled_condition == 'instance-and-formatted-content':
                if not isinstance(content, Tag) or not element_to_formatted_text.element_to_formatted_text(content):
                    continue
            else:
                if filled_condition in content.get("class", []):
                    continue

            news = {
                "title": news["title"],
                "content": f"""{news["content"]}
                {content.text.strip()}""",
                "link": news["link"],
                "date": news["date"]
            }
        return news
    
    def load_detik_news(self, stock_name, position, company_pattern):
        browser = Browser()
        url = f"{self.media_url["detik"]}?page=1"
        news = []
        loaded_all = False
        response = browser.session.get(url)
        paginations = browser.get_element(response.text, "a", "pagination__item")
        total_page = self.get_paginate_based_on_biggest_number_element(paginations)

        pbar_pages =  tqdm(
            total=total_page,
            desc=f"DETIK {stock_name} Page {position}",
            position=position,
            leave=True
        )
        position+=1

        for i in range(total_page):
            if loaded_all:
                pbar_pages.update(total_page - pbar_pages.n)
                break
            
            if i != 0:
                response = browser.session.get(f"{self.media_url["detik"]}?page={i+1}")

            for link in browser.get_element(response.text, element="a", class_element="media__link"):
                text = link.text.strip()
                date_div = browser.get_element(
                    link.parent, 
                    class_element="media__date", 
                    is_find_all=False, 
                    is_find_sibling=True, 
                    init_element=False
                )

                if not date_div:
                    continue

                publish_date = None
                success = True
                def match_1(_):
                    nonlocal publish_date
                    publish_date = datetime.today().strftime("%Y-%m-%d")

                def match_2(match):
                    nonlocal publish_date
                    hari, bulan_str, tahun = match.groups()
                    publish_date = f"{tahun}-{self.months[bulan_str]}-{hari.zfill(2)}"
                
                def failed_all(_):
                    nonlocal success
                    success = False

                def match_1_error(_):
                    nonlocal date_div, failed_all, match_2
                    matching.matching(r'(\d{1,2})\s+(\w{3})\s+(\d{4})', date_div.text.strip(), match_2, failed_all)
                

                matching.matching(r'(\d+)\s+(\w+)\s+yang\s+lalu', date_div.text.strip(), match_1, match_1_error)
                
                if not success or "finance.detik.com" not in link.get('href'):
                    continue
                
                if self.append_new_news(news, link.get('href'), publish_date, text, stock_name, company_pattern):
                    loaded_all = True
                    break

            pbar_pages.update(1)
        pbar_pages.close()    
        
        pbar_articles = tqdm(
            total=len(news),
            desc=f"DETIK {stock_name} Article {position}",
            position=position,
            leave=True
        )
        position+=1

        def process_article(n):
            process_browser = Browser()
            response = process_browser.session.get(news[n]["link"])
            contents = process_browser.get_element(response.text, 'p')
            if contents is not None:
                return self.fetch_news_article(contents, news[n], "para_caption")
            
            return news[n]
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(process_article, n): n for n in range(len(news))
            }

            for future in as_completed(futures):
                n = futures[future]
                news[n] = future.result()
                pbar_articles.update(1)
        
        pbar_articles.close()
        return news
    
    def load_cnn_indonesia_news(self, stock_name, position, company_pattern):
        browser = Browser()
        url = f"{self.media_url["cnnindonesia"]}?page=1"
        response = browser.session.get(url)
        news = []
        loaded_all = False
        paginations = browser.get_element(html=response.text, element='a', attrs={'dtr-evt': 'halaman'})
        total_page = self.get_paginate_based_on_biggest_number_element(paginations)
        
        pbar_pages =  tqdm(
            total=total_page,
            desc=f"CNN {stock_name} Page {position}",
            position=position,
            leave=True
        )

        position+=1

        for i in range(total_page):
            if loaded_all:
                pbar_pages.update(total_page - pbar_pages.n)
                break   

            if i != 0:
                response = browser.session.get(f"{self.media_url["cnnindonesia"]}?page={i+1}")

            articles = browser.get_element(response.text, 'article', class_element="flex-grow")
            if not articles:
                pbar_pages.update(1)
                continue

            for article in articles:
                link = browser.get_element(
                    article, "a", 
                    attrs={'aria-label': 'link description'}, 
                    is_find_all=False, 
                    init_element=False
                )

                try:
                    cleaned_contents = browser.get_element(link.contents, is_find_all=False, init_element=False, is_find_sibling=False, is_find_child=True)
                    text = cleaned_contents[1]["child"][0]["parent"].text.strip()
                    publish_date = cleaned_contents[1]["child"][1]["child"][1]["parent"].text.strip()
                except IndexError:
                    continue

                success = True
                def match_1(match_result):
                    nonlocal publish_date
                    publish_date = datetime.today()
                    nominal, type_data = match_result.groups()
                    nominal = int(nominal)
                    match type_data:
                        case "hari":
                            publish_date -= timedelta(days=nominal)
                        case "minggu":
                            publish_date -= timedelta(weeks=nominal)
                        case "bulan":
                            publish_date -= relativedelta(months=nominal)
                    
                    publish_date = publish_date.strftime("%Y-%m-%d")

                def match_2(match):
                    nonlocal publish_date
                    hari, bulan_str, tahun = match.groups()
                    publish_date = f"{tahun}-{self.months[bulan_str]}-{hari.zfill(2)}"
                
                def failed_all(_):
                    nonlocal success
                    success = False

                def match_1_error(_):
                    nonlocal failed_all, match_2, publish_date
                    matching.matching(r'(\d{1,2})\s+(\w{3})\s+(\d{4})', publish_date, match_2, failed_all)
                

                matching.matching(r'\s*(\d+)\s+(\w+)\s+yang\s+lalu', publish_date, match_1, match_1_error)
                if not success:
                    continue
                
                if self.append_new_news(news, link.get('href'), publish_date, text, stock_name, company_pattern):
                    loaded_all = True
                    break
            pbar_pages.update(1)
        pbar_pages.close()

        pbar_articles = tqdm(
            total=len(news),
            desc=f"CNN {stock_name} Article {position}",
            position=position,
            leave=True
        )

        def process_article(n):
            process_browser = Browser()
            response = process_browser.session.get(news[n]["link"])
            contents = process_browser.get_element(response.text, 'p')
            if contents is not None:
                return self.fetch_news_article(contents, news[n], "empty-class")

            return news[n]
            
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {
                executor.submit(process_article, n): n for n in range(len(news))
            }

            for future in as_completed(futures):
                n = futures[future]
                news[n] = future.result()
                pbar_articles.update(1)
    
        pbar_articles.close()
        return news
    
    def load_bisnis_com(self, category, stock_name, position, company_pattern):
        browser = Browser()
        total_page = 1
        response = browser.session.get(f"{self.media_url["bisnis"]}?categoryId={category}&page=1")

        try:
            paginations = browser.get_element(response.text, 'p', class_element="pagingLabel", is_find_all=False)
            match = matching.matching(r'dari\s+(\d+)\s+halaman', paginations.text.strip())
            if not match:
                raise ValueError("Pagination label not found")
            total_page = int(match.group(1))
            news = []
            loaded_all = False
            pbar_pages =  tqdm(
                total=total_page,
                desc=f"Bisnis {stock_name} Page {position}",
                position=position,
                leave=True
            )
            position+=1

            for i in range(total_page):
                if loaded_all:
                    pbar_pages.update(total_page - pbar_pages.n)
                    break

                if i != 0:
                    response = browser.session.get(f"{self.media_url["bisnis"]}?categoryId={category}&page={i+1}")

                links = browser.get_element(response.text, 'div', class_element="artContent")
                if not links:
                    pbar_pages.update(1)
                    continue
                
                for link in links:
                    link_element = browser.get_element(link, 'a', class_element='artLink', init_element=False, is_find_all=False)
                    if not link_element:
                        continue

                    base_url = link_element.get('href')

                    title_element = browser.get_element(link_element, class_element='artTitle', init_element=False, is_find_all=False)
                    date_element = browser.get_element(link_element, class_element='artDate', init_element=False, is_find_all=False)
                    if not title_element or not date_element:
                        continue

                    text = title_element.text.strip()
                    publish_date = date_element.text.strip()

                    success = True
                    def match_1(_):
                        nonlocal publish_date
                        publish_date = datetime.today().strftime("%Y-%m-%d")

                    def match_2(match):
                        nonlocal publish_date
                        hari, bulan_str, tahun, _, _ = match.groups()
                        publish_date = f"{tahun}-{self.months[bulan_str]}-{hari.zfill(2)}"
                    
                    def failed_all(_):
                        nonlocal success
                        success = False

                    def match_1_error(_):
                        nonlocal failed_all, match_2, publish_date
                        matching.matching(r'(\d{1,2})\s+(\w{3})\s+(\d{4})(?:\s*\|\s*(\d+):(\d+)\s+WIB)?', publish_date, match_2, failed_all)
                    

                    matching.matching(r'(\d+)\s+(\w+)\s+yang\s+lalu', publish_date, match_1, match_1_error)
                    if not success:
                        continue

                    if self.append_new_news(news, base_url, publish_date, text, stock_name, company_pattern):
                        loaded_all = True
                        break
                pbar_pages.update(1)
            pbar_pages.close()

            pbar_articles =  tqdm(
                total=len(news),
                desc=f"Bisnis {stock_name} Article {position}",
                position=position,
                leave=True
            )

            def process_article(n):
                process_browser = Browser()
                response = process_browser.session.get(news[n]["link"])
                article = process_browser.get_element(response.text, 'article', class_element="detailsContent", is_find_all=False)
                if article is not None:
                    contents = process_browser.get_element(article, 'p', init_element=False)
                    if contents is not None:
                        return self.fetch_news_article(contents, news[n], "empty-class")
                
                return news[n]
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {
                    executor.submit(process_article, n): n for n in range(len(news))
                }

                for future in as_completed(futures):
                    n = futures[future]
                    news[n] = future.result()
                    pbar_articles.update(1)
                
            pbar_articles.close()  
            return news
        except Exception as e:
            print(e)
            return []
    
    def load_tribun_news(self, category, stock_name, position, company_pattern):
        browser = Browser()
        total_page = 1
        response = browser.session.get(f"{self.media_url["tribunnews"]}{category}?page=1")

        try:
            pagination_links = browser.get_element(response.text, 'a', attrs={'data-ci-pagination-page': True})
            if not pagination_links:
                raise ValueError("Tidak ada link pagination")
            
            total_page = max(int(link['data-ci-pagination-page']) for link in pagination_links)
            news = []

            loaded_all = False
            pbar_pages =  tqdm(
                total=total_page,
                desc=f"TribunNews {stock_name} Page {position}",
                position=position,
                leave=True
            )

            position+=1

            for i in range(total_page):
                if loaded_all:
                    pbar_pages.update(total_page - pbar_pages.n)
                    break

                if i != 0:
                    response = browser.session.get(f"{self.media_url["tribunnews"]}{category}?page={i+1}")

                news_list_container = browser.get_element(response.text, 'ul', class_element="lsi", is_find_all=False)
                if not news_list_container:
                    pbar_pages.update(1)
                    continue

                for link in browser.get_element(news_list_container, 'li', init_element=False):
                    link_element = browser.get_element(link, 'h3', init_element=False, is_find_all=False)
                    date_div = browser.get_element(link, 'time', init_element=False, is_find_all=False)
                    if not link_element or not date_div:
                        continue

                    text_element = browser.get_element(link_element, 'a', init_element=False, is_find_all=False)

                    if not text_element:
                        continue
                    
                    base_url = text_element.get('href')
                    text = text_element.get('title')
                    publish_date = date_div.text.strip()

                    success = True
                    def match_1(match):
                        nonlocal publish_date
                        tanggal, bulan_str, tahun, _, _ = match.groups()
                        publish_date = f"{tahun}-{self.months[bulan_str]}-{tanggal.zfill(2)}"

                    def failed_all(_):
                        nonlocal success
                        success = False

                    matching.matching(r'(?:\w+,\s*)?(\d{1,2})\s+(\w+)\s+(\d{4})\s+(\d{2}):(\d{2})\s+WIB', publish_date, match_1, failed_all)                    
                    if not success:
                        continue
                    
                    if self.append_new_news(news, base_url, publish_date, text, stock_name, company_pattern):
                        loaded_all = True
                        break
                pbar_pages.update(1)
            pbar_pages.close()

            pbar_articles =  tqdm(
                total=total_page,
                desc=f"Tribunnews {stock_name} Articles {position}",
                position=position,
                leave=True
            )

            def process_article(n):
                process_browser = Browser()
                response = process_browser.session.get(news[n]["link"])
                contents_element = process_browser.get_element(response.text, class_element="side-article", is_find_all=False)
                if contents_element is not None:
                    contents = process_browser.get_element(contents_element, 'p', init_element=False)
                    return self.fetch_news_article(contents, news[n], "empty-class")
                return news[n]
                        
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {
                    executor.submit(process_article, n): n for n in range(len(news))
                }

                for future in as_completed(futures):
                    n = futures[future]
                    news[n] = future.result()
                    pbar_articles.update(1)

            pbar_articles.close()  
            return news
        except Exception as e:
            print(e)
            return []
    
    def load_idx_news(self, stock_name, position, company_pattern):
        browser = Browser(True)
        browser.driver.get(f"{self.media_url['idxnews']}/id/berita/berita/?p=1")
        
        try:
            browser.driver.execute_script(self.EXECUTE_SCRIPT)
            html = None
            def assign_html(html_data):
                nonlocal html
                html = html_data

            browser.load_page_element(element="a.card-title", is_sleep=True, callback=assign_html)
            if html is None:
                print("IDX None")
                return
            
            loaded_all = False
            len_page = 0
            news = []

            pages = browser.get_element(html, 'li')
            links = browser.get_element(html, 'a', class_element="card-title")

            def define_len_page(match):
                nonlocal len_page

                num_text = match.group(1)
                len_page = int(num_text)

            for page in pages:
                text = page.text.strip()
                matching.matching(r'dari\s+(\d+)', text, define_len_page)
            
            pbar_pages =  tqdm(
                total=len_page,
                desc=f"IDX {stock_name} Page {position}",
                position=position,
                leave=True
            )

            position+=1

            for i in range(len_page):
                if loaded_all:
                    pbar_pages.update(len_page - pbar_pages.n)
                    break

                if i != 0:
                    browser.driver.get(f"{self.media_url['idxnews']}/id/berita/berita/?p={i+1}")
                    browser.driver.execute_script(self.EXECUTE_SCRIPT)
                    html = None
                    def assign_html(html_param):
                        nonlocal html
                        html = html_param
    
                    browser.load_page_element(element='a.card-title', is_sleep=True, callback=assign_html)
                    if html is None:
                        pbar_pages.update(1)
                        continue

                    links = browser.get_element(html, 'a', "card-title")
                
                for link in links:
                    title = link.text.strip()

                    date_div = browser.get_element(link, 'small', init_element=False, is_find_all=False, is_find_sibling=True, is_next_sibling=False)
                    def match_1(match):
                        nonlocal link, title, loaded_all
                        date, month, year = match.groups()
                        publish_date = f"{year}-{self.months[month]}-{date.zfill(2)}"

                        if self.append_new_news(news, link.get('href'), publish_date, title, stock_name, company_pattern):
                            loaded_all = True
                    
                    matching.matching(r'(\d{2})\s+(\w+)\s+(\d{4})', date_div.text.strip(), match_1)
                    if loaded_all:
                        break

                pbar_pages.update(1)
            pbar_pages.close()

            pbar_articles =  tqdm(
                total=len(news),
                desc=f"IDX {stock_name} Article {position}",
                position=position,
                leave=True
            )
            position+=1

            def process_article(n):
                process_browser = Browser(True)
                
                process_browser.driver.get(f"{self.media_url['idxnews']}{news[n]['link']}")
                process_browser.driver.execute_script(self.EXECUTE_SCRIPT)
                
                html = None
                def assign_html(html_data):
                    nonlocal html
                    html = html_data

                process_browser.load_page_element(element="article.clearfix", is_sleep=True, callback=assign_html)
                return self.fetch_news_article(process_browser.get_element(html, 'article', is_find_all=False).children, news[n], "instance-and-formatted-content")
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {
                    executor.submit(process_article, n): n for n in range(len(news))
                }

                for future in as_completed(futures):
                    n = futures[future]
                    news[n] = future.result()
                    pbar_articles.update(1)
            
            pbar_articles.close()
            return news
        except Exception as e:
            print(e)
            return []
        finally:
            browser.driver.quit()