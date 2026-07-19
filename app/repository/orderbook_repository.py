import pandas as pd

from datetime import datetime, timedelta

from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from config import config, Browser
from database import StockDB
from flask import current_app as app

class OrderbookRepository:
    def __init__(self, is_init=False):
        self.orderbook = {}
        self.newest_date = {}

        if is_init:
            self.load_orderbook_data()

    def get_orderbook(self, stock_name):
        if self.orderbook is None:
            return []
        
        if self.orderbook[stock_name] is None:
            return []
        
        return self.orderbook[stock_name]

    def load_orderbook_data(self):
        with app.app_context():
            stocks = [
                stock.code for stock in StockDB.query.all()
            ]

        if len(stocks) == 0:
            self.orderbook = None
        else:
            for stock in stocks:
                try:
                    self.orderbook[stock] = pd.read_csv(f'data/OrderBook/{stock}.csv')
                    if 'Unnamed: 0' in self.orderbook[stock].columns:
                        self.orderbook[stock].drop('Unnamed: 0', axis=1, inplace=True)
                except FileNotFoundError:
                    self.orderbook[stock] = None

    def update_orderbook_data(self):
        with app.app_context():
            stocks = [
                stock.code for stock in StockDB.query.all()
            ]

        for stock in stocks:
            if 'date' in self.orderbook[stock].columns:
                self.orderbook[stock]['date'] = pd.to_datetime(self.orderbook[stock]['date']).dt.date
                self.newest_date[stock] = self.orderbook[stock]['date'].max().strftime("%Y-%m-%d")

                if pd.isna(self.newest_date[stock]):
                    self.newest_date[stock] = datetime.strptime(config.start, "%Y-%m-%d")
                else:
                    self.newest_date[stock] = datetime.strptime(self.newest_date[stock], "%Y-%m-%d")    
            else:
                self.newest_date[stock] = datetime.strptime(config.start, "%Y-%M-%d")

        self.load_orderbook_all_stock_data(stocks)

    def load_orderbook_all_stock_data(self, stocks):
        start_str = datetime.strftime(min(self.newest_date.values()), "%Y-%m-%d")
        end_str = config.end
        ranges = self.split_date_range(start_str, end_str)
        self.browser = [None] * len(ranges)
        new_orderbook = []
        load_position = 0
        with ThreadPoolExecutor() as executor:
            futures = []

            for start_range, end_range in ranges:
                futures.append(executor.submit(self.load_orderbook, start_range, end_range, load_position, stocks))
                load_position += 1

            for f in as_completed(futures):
                new_orderbook.extend(f.result())
        
        stocks_data = {stock: [] for stock in stocks}
        for date_dict in new_orderbook:  
            for stock, data in date_dict.items():
                stocks_data[stock].append(data)
        
        for stock in stocks:
            if not stocks_data[stock]:
                continue

            new_df = pd.DataFrame(stocks_data[stock])
            if self.orderbook[stock] is None:
                self.orderbook[stock] = new_df
            else:
                self.orderbook[stock] = pd.concat([self.orderbook[stock], new_df], ignore_index=True)
                self.orderbook[stock] = self.orderbook[stock].drop_duplicates(subset=['date'], keep='last')
            
            self.orderbook[stock]['date'] = pd.to_datetime(self.orderbook[stock]['date']).dt.date
            self.orderbook[stock] = self.orderbook[stock].sort_values(by='date').reset_index(drop=True)
            self.orderbook[stock] = self.orderbook[stock].drop_duplicates()
            self.orderbook[stock].to_csv(f'./data/OrderBook/{stock}.csv')

    
    def split_date_range(self, start_str, end_str):
        start = datetime.strptime(start_str, "%Y-%m-%d")
        end = datetime.strptime(end_str, "%Y-%m-%d")
        ranges = []
        current = start
        while current <= end:
            year = current.year
            year_end = min(datetime(year, 12, 31), end)
            ranges.append((current.strftime("%Y-%m-%d"), year_end.strftime("%Y-%m-%d")))
            current = year_end + timedelta(days=1)
        return ranges
    
    def setup_columns(self, position):
        try:
            button = self.browser[position].wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'btn-filter-input') and contains(.,'Kolom')]")))
            button.click()

        except Exception as e:
            print("Gagal buka panel kolom:", e)
            return

        def set_column_state(label_text, check_it):
            xpath = f"//label[.//span[@class='check-text' and text()='{label_text}']]"
            label_elem = self.browser[position].driver.find_element(By.XPATH, xpath)
            is_checked = "is-checked" in label_elem.get_attribute("class")
            if (check_it and not is_checked) or (not check_it and is_checked):
                checkbox = label_elem.find_element(By.TAG_NAME, "input")
                self.browser[position].driver.execute_script("arguments[0].click();", checkbox)

        check_list = ["Foreign Sell", "Foreign Buy", "Offer", "Offer Volume", "Bid", "Bid Volume"]

        for col in check_list:
            set_column_state(col, check_it=True)


        implement_button = self.browser[position].driver.find_element(By.XPATH, "//button[contains(@class,'btn--primary') and contains(.,'Terapkan')]")
        self.browser[position].driver.execute_script("arguments[0].click();", implement_button)
        return True
    
    def extract_data_from_idx_thead(self, table):
        thead = table.find('thead')
        headers = []
        if thead:
            ths = thead.find_all('th')
            for th in ths[1:]:
                span = th.find('span')
                if span:
                    headers.append(span.get_text(strip=True))
        
        return headers
    
    def extract_data_from_idx_tbody(self, table, headers):
        data_rows = []
        tbody = table.find('tbody')
        if not tbody:
            return []
        
        rows = tbody.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if not cells:
                continue

            row_data = {}
            for idx, cell in enumerate(cells):
                span = cell.find('span')
                value = span.get_text(strip=True) if span else cell.get_text(strip=True)
                if idx < len(headers):
                    row_data[headers[idx]] = value
                    
            if row_data:
                data_rows.append(row_data)
            
        return data_rows
    
    def extract_data_from_idx_table(self, table, stocks):
        headers = self.extract_data_from_idx_thead(table)
        data_rows = self.extract_data_from_idx_tbody(table, headers)
        
        result_list = [item for item in data_rows if item.get('Kode Saham') in set(stocks)]
        if not result_list:
            return None

        return result_list
    
    def mapping_data(self, result_list, target_date, stocks):
        item = result_list[0]
        required_keys = ['Nilai', 'Offer', 'Offer Volume', 'Bid', 'Bid Volume', 'Foreign Sell', 'Foreign Buy']
        if any(key not in item for key in required_keys):
            raise Exception("Column not found")
        
        result = {}
        for stock in stocks:
            for r in result_list:
                if r.get('Kode Saham') == stock:               
                    result[stock] = {
                        'date': target_date.strftime('%Y-%m-%d'),
                        'value': self.to_int(r.get('Nilai')),
                        'offer_value': self.to_int(r.get('Offer')),
                        'offer_volume': self.to_int(r.get('Offer Volume')),
                        'bid_value': self.to_int(r.get('Bid')),
                        'bid_volume': self.to_int(r.get('Bid Volume')),
                        'foreign_sell': self.to_int(r.get('Foreign Sell')),
                        'foreign_buy': self.to_int(r.get('Foreign Buy'))
                    }
        return result

    def scrape_date(self, target_date, position, stocks):
        date_input = self.browser[position].wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.mx-input")))
        self.browser[position].driver.execute_script("arguments[0].value = '';", date_input)
        self.browser[position].driver.execute_script(f"arguments[0].value = '{target_date.strftime('%Y-%m-%d')}';", date_input)
        self.browser[position].driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", date_input)
        self.browser[position].driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", date_input)

        select_elem = self.browser[position].wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "select.footer__row-count__select")))
        self.browser[position].driver.execute_script("arguments[0].value = '-1';", select_elem)
        self.browser[position].driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", select_elem)
        self.browser[position].wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#vgt-table tbody tr")))

        table = self.browser[position].get_element(self.browser[position].driver.page_source, "table", id="vgt-table", is_find_all=False)
        if not table:
            return None
        
        result_list = self.extract_data_from_idx_table(table, stocks)
        if result_list is None:
            return None

        return self.mapping_data(result_list, target_date, stocks)
    
    def to_int(self, val):
        if val is None:
            return 0 
        if isinstance(val, (int, float)):
            return int(val)
        
        cleaned = str(val).strip().replace('.', '').replace(',', '')
        if cleaned == '':
            return 0
        return int(cleaned)
    
    def load_orderbook(self, start_str, end_str, position, stocks):
        current_date = datetime.strptime(start_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_str, "%Y-%m-%d")
        total_days = (end_date - current_date).days + 1
        orderbook = []
        self.browser[position] = Browser(True)
        self.browser[position].driver.get(config.orderbook_url)

        if not self.setup_columns(position):
            raise Exception("Gagal setup kolom")

        with tqdm(total=total_days, position=position, desc="Load OrderBook") as pbar:
            while current_date <= end_date:
                try:
                    result = self.scrape_date(current_date, position, stocks)
                    if result:
                        orderbook.append(result)
                    
                    current_date += timedelta(days=1)
                    pbar.update(1)
                    if current_date.weekday() >= 5:
                        current_date += timedelta(days=2)
                        pbar.update(2)
                    
                except Exception:
                    try:
                        self.browser[position].driver.quit()
                    except Exception:
                        pass
                    self.browser[position] = Browser(True)
                    self.browser[position].driver.get(config.orderbook_url)
                    if not self.setup_columns(position):
                        raise Exception("Gagal setup kolom")
                    continue
        
        self.browser[position].driver.quit()
        return orderbook