from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import requests
from fake_useragent import UserAgent

class Browser:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    parser = "lxml"
    max_retries = 3

    def __init__(self, is_using_browser = False):
        self.init_function(is_using_browser)
    
    def init_function(self, is_using_browser):
        try:
            if is_using_browser:
                options = webdriver.ChromeOptions()
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--headless=new")
                options.add_argument("--disable-web-security")
                options.add_argument("--disable-features=IsolateOrigins,site-per-process")
                ua = UserAgent()
                options.add_argument(f'user-agent={ua.random}')
                options.add_experimental_option("excludeSwitches", ['enable-automation'])
                options.add_experimental_option("useAutomationExtension", False)
                options.add_argument("--disable-notifications")

                self.driver = webdriver.Chrome(options=options)
                self.wait = WebDriverWait(self.driver, 60)
            else:
                self.session = requests.Session()
                self.session.headers.update(self.headers)
        except Exception as e:
            print(e)
            self.init_function(is_using_browser)

    def filters_class_params(self, class_element, attrs, id):
        filters = {}
        if class_element is not None:
            filters['class_'] = class_element
        if attrs is not None:
            filters['attrs'] = attrs
        if id is not None:
            filters['id'] = id
        
        return filters
    
    def get_element_find_all(self, element, soup, filters):
        if element is not None:
            return soup.find_all(element, **filters)
        else:
            return soup.find_all(**filters)
    
    def get_element_find_sibling(self, element, soup, filters, is_next_sibling):
        if element is not None:
            return soup.find_next_sibling(element, **filters) if is_next_sibling else soup.find_previous_sibling(element, **filters)
        else:
            return soup.find_next_sibling(**filters) if is_next_sibling else soup.find_previous_sibling(**filters)

    def get_element_find(self, element, soup, filters):
        if element is not None:
            return soup.find(element, **filters)
        else:
            return soup.find(**filters)

    def get_element(self, html, element = None, class_element = None, attrs = None, is_find_all = True, is_find_sibling = False, is_next_sibling = True, init_element = True, is_find_child = False, id = None):
        if init_element:
            soup = BeautifulSoup(html, self.parser)
        else:
            soup = html

        filters = self.filters_class_params(class_element, attrs, id)

        if is_find_all:
            return self.get_element_find_all(element, soup, filters)
            
        if is_find_sibling:
            return self.get_element_find_sibling(element, soup, filters, is_next_sibling)
                
        if is_find_child:
            return self.generate_child(soup)

        if not is_find_all and not is_find_sibling and not is_find_child:
            return self.get_element_find(element, soup, filters)

    def generate_child(self, elements):
        result = [] 
        for el in elements:
            if isinstance(el, str):
                continue
            
            node = {
                "parent": el,
                "child": []
            }
            
            if hasattr(el, 'contents') and el.contents:
                node["child"] = self.generate_child(el.contents)
            
            result.append(node)
        
        return result

    def load_page_element(self, element, is_sleep = False, wait_action = EC.presence_of_element_located, by = By.CSS_SELECTOR, callback = None, *callback_args, **callback_kwargs):
        for _ in range(self.max_retries):
            try:
                self.wait.until(wait_action((by, element)))
                break
            except TimeoutException:
                self.driver.refresh()
                time.sleep(3)
        else:
            if callback:
                callback(None, *callback_args, **callback_kwargs)
            return
        
        if is_sleep:
            time.sleep(2)

        if callback:
            callback(self.driver.page_source, *callback_args, **callback_kwargs)