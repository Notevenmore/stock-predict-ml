from .news_repository import NewsRepository
from config import config

import threading
import re
from tqdm import tqdm
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import torch
import ast
import os

from indoNLP.preprocessing import replace_slang
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModel
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import joblib
import spacy

class ProcessedDataRepository:
    def __init__(self):
        self.news_repository = NewsRepository()
        self.new_news = {}
        self.processed_news = {}
        self.scaler = None
        self.pca = None
        
        self._thread_local = threading.local()
        self._stemmer = StemmerFactory().create_stemmer()
        self._stopword = StopWordRemoverFactory().create_stop_word_remover()
        
        self.load_embedded_data()

    def get_processed_news_data(self, stock_name):
        if self.processed_news is None:
            return []
        
        if self.processed_news[stock_name] is None:
            return []
        
        return self.processed_news

    def load_embedded_data(self):
        for stock_name in config.stocks:
            try:
                self.processed_news[stock_name] = pd.read_csv(f'data/Processed-News/{stock_name}.csv')
                self.processed_news[stock_name].select_dtypes('number').fillna(0)
            except FileNotFoundError:
                self.processed_news[stock_name] = None

    def __load_new_news(self, stock_name):
        self.new_news[stock_name] = []
        all_processed_news = set()

        if self.news_repository.news[stock_name] is None:
            return
        
        if self.processed_news.get(stock_name) is None:
            self.new_news[stock_name] = self.news_repository.news[stock_name]
            return
        
        for processed in self.processed_news[stock_name]["title"]:
            if isinstance(processed, str):
                try:
                    titles = ast.literal_eval(processed)
                    if isinstance(titles, list):
                        all_processed_news.update(titles)
                except Exception:
                    all_processed_news.add(processed)
            elif isinstance(processed, list):
                all_processed_news.update(processed)
                
        for _, news in self.news_repository.news[stock_name].iterrows():
            if news["title"] not in all_processed_news:
                self.new_news[stock_name].append(news)
        
        self.new_news[stock_name] = pd.DataFrame(self.new_news[stock_name])

    def save_embedded_data(self):
        if self.news_repository.news is not None:
            for stock_name in config.stocks:
                self.__load_new_news(stock_name)
                if self.new_news[stock_name] is not None and not self.new_news[stock_name].empty:
                    self.embed_data_workflow(stock_name)
        else:
            self.processed_news = None

    def embed_data_workflow(self, stock_name):
        news = self.new_news[stock_name]
        position = 0
        news = self.manage_data(news, 'title', 'content', stock_name, "Standarization", position, "title_clean", "content_clean", self.standarization_data)
        news = self.manage_data(news, "title_clean", "content_clean", stock_name, "Abbreviation Processing", position, "title_abbreviation", "content_abbreviation", self.abbreviation_processing)
        news = self.manage_data(news, "title_abbreviation", "content_abbreviation", stock_name, "Pipeline NER", position, "title_entity", "content_entity", self.pipeline_ner)
        news = self.manage_data(news, "title_abbreviation", "content_abbreviation", stock_name, "Stopword", position, "title_stopword_removed", "content_stopword_removed", self.handle_stopword)
        news = self.manage_data(news, "title_stopword_removed", "content_stopword_removed", stock_name, "Stemming", position, "title_stemmed", "content_stemmed", self.stem_word)
        
        tokenizer = AutoTokenizer.from_pretrained("indobenchmark/indobert-base-p1")
        news = self.prepare_and_tokenize(tokenizer, news)

        model = AutoModelForSequenceClassification.from_pretrained('agufsamudra/indo-sentiment-analysis').to(config.device)
        model.eval()
        news[['sentiment_label', 'sentiment_score']] = news.apply(lambda x: pd.Series(self.get_sentiment(x['input_ids'], x['attention_mask'], model)), axis=1)

        model = AutoModel.from_pretrained("indobenchmark/indobert-base-p1").to(config.device)
        model.eval()
        embeddings = self.get_embeddings_from_dataframe(news, model)
        news['embedding'] = list(embeddings)
        news = self.grouped_news(news)

        news['date'] = pd.to_datetime(news['date']).astype('datetime64[s]')

        is_initialized = self.__load_pca(stock_name)
        old_data = pd.DataFrame()
        if self.processed_news is not None and self.processed_news[stock_name] is not None:
            old_data = self.processed_news[stock_name].copy()
            def parse_embedding(x):
                if isinstance(x, str) and x.startswith('['):
                    try:
                        return np.array(ast.literal_eval(x))
                    except Exception:
                        numbers = re.findall(r'[-+]?\d*\.?\d+[eE]?[-+]?\d*', x)
                        if numbers:
                            return np.array([float(n) for n in numbers])
                return x
            if 'emb_mean' in old_data.columns:
                old_data['emb_mean'] = old_data['emb_mean'].apply(parse_embedding)
            
            if 'embedding' in old_data.columns:
                old_data['embedding'] = old_data['embedding'].apply(parse_embedding)
                
        if is_initialized:
            news = self.normalization_data(news)
            news = pd.concat([old_data, news])
        else:
            pca_cols = [col for col in old_data.columns if col.startswith('sentiment_pca_')]
            old_data = old_data.drop(columns=pca_cols)
            
            news = pd.concat([old_data, news], ignore_index=True)
            news = self.normalization_data(news, stock_name, True)
            news = news.drop_duplicates(subset=['date'], keep='last')
        news.to_csv(f'data/Processed-News/{stock_name}.csv', index=False)
    
    def manage_data(self, news, title_key, content_key, stock_name, process_name, position, title_target_process_name, content_target_process_name, process):
        with ThreadPoolExecutor() as executor:
            futures = {}
            for i, title in enumerate(news[title_key]):
                futures[executor.submit(process, title)] = ('title', i)
            for i, content in enumerate(news[content_key]):
                futures[executor.submit(process, content)] = ('content', i)

            total = len(futures)
            result_title = [None] * len(news[title_key])
            result_content = [None] * len(news[content_key])

            with tqdm(total=total, desc=f"{process_name} {stock_name}", leave=True, position=position) as pbar:
                for future in as_completed(futures):
                    typ, idx = futures[future]
                    result = future.result()
                    if typ == 'title':
                        result_title[idx] = result
                    else:
                        result_content[idx] = result
                    pbar.update(1)

            news[title_target_process_name] = result_title
            news[content_target_process_name] = result_content

            return news
    
    def standarization_data(self, text):
        if not isinstance(text, str):
            return ""
        
        text = text.lower()
        pola_persen = r'(\d+),(\d+)\s*%'
        def change_word_to_number(match):
            front = match.group(1)
            back = match.group(2)
            return f"{front} koma {back} persen"
        
        pola_rupiah = r'rp\.?\s*([\d\.]+)'
        def rupiah_formatter(match):
            angka_bersih = match.group(1).replace('.', '')
            return f"{angka_bersih} rupiah"
            
        text = re.sub(pola_rupiah, rupiah_formatter, text)
        text = re.sub(pola_persen, change_word_to_number, text)
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        text = re.sub(r'@\S+', '', text)
        text = re.sub(r'#\S+', '', text)
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\bcom\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bdot\b', '.', text, flags=re.IGNORECASE)

        for word in config.media_keywords:
            text = re.sub(r'\b' + re.escape(word) + r'\b', '', text, flags=re.IGNORECASE)

        text = re.sub(r'\s+', ' ', text)

        return text.strip()
    
    def abbreviation_processing(self, text):
        return replace_slang(text)
    
    def _get_nlp(self):
        if not hasattr(self._thread_local, "nlp"):
            self._thread_local.nlp = spacy.load("id_ner_spacy_indonesian")
        return self._thread_local.nlp

    def pipeline_ner(self, text):
        if not isinstance(text, str) or not text.strip():
            return [] 
        nlp = self._get_nlp()
        doc = nlp(text)
        return [(ent.text, ent.label_) for ent in doc.ents]
    
    def get_stopword_remover(self):
        factory = StopWordRemoverFactory()
        stopword_remover = factory.create_stop_word_remover()

        return stopword_remover
    
    def handle_stopword(self, text):
        return self._stopword.remove(text) 
    
    def get_stemmer_factory(self):
        factory = StemmerFactory()
        stemmer = factory.create_stemmer(True)

        return stemmer

    def stem_word(self, text):
        return self._stemmer.stem(text)

    def prepare_and_tokenize(self, tokenizer, news_item, max_length=512):
        news_item['full_text'] = news_item['title_stemmed'].fillna('').astype(str) + " " + news_item['content_stemmed'].fillna('').astype(str)
        news_item['full_text'] = news_item['full_text'].str.strip()

        news_item.loc[news_item['full_text'] == '', 'full_text'] = tokenizer.unk_token
        
        encoding = tokenizer(
            news_item['full_text'].tolist(),
            max_length=max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )

        news_item['input_ids'] = encoding['input_ids'].squeeze().tolist()
        news_item['attention_mask'] = encoding['attention_mask'].squeeze().tolist()

        return news_item
    
    def get_sentiment(self, input_ids, attention_mask, model):
        if not input_ids or len(input_ids) == 0:
            return 'UNKNOWN', 0.0
        
        input_ids_tensor = torch.tensor([input_ids], dtype=torch.long).to(config.device)
        attention_mask_tensor = torch.tensor([attention_mask], dtype=torch.long).to(config.device)

        with torch.no_grad():
            outputs = model(input_ids=input_ids_tensor, attention_mask=attention_mask_tensor)
        
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)
        pred_id = torch.argmax(probs, dim=-1).item()
        score = probs[0][pred_id].item()

        label = 'POSITIVE' if pred_id == 1 else 'NEGATIVE'
        return label, score
    
    def get_embeddings_from_dataframe(self, df, model, batch_size=32):
        num_rows = len(df)
        embeddings = []

        input_ids_list = df['input_ids'].tolist()
        attention_mask_list = df['attention_mask'].tolist()

        for start in tqdm(range(0, num_rows, batch_size)):
            end = min(start + batch_size, num_rows)
            batch_input_ids = input_ids_list[start:end]
            batch_attention_mask = attention_mask_list[start:end]

            input_ids = torch.tensor(batch_input_ids).to(config.device)
            attention_mask = torch.tensor(batch_attention_mask).to(config.device)

            with torch.no_grad():
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                batch_emb = outputs.pooler_output.cpu().numpy()

            embeddings.append(batch_emb)

        return np.vstack(embeddings)
    
    def mean_sentiment_score(self, row, sentiment):
        scores = row['sentiment_score']
        labels = row['sentiment_label']
        total = 0
        count = 0
        for label, score in zip(labels, scores):
            if label == sentiment:
                total += score
                count += 1
        return total / count if count > 0 else 0.0
    
    def grouped_news(self, news):
        grouped_news = news.groupby('date', as_index=False).agg({
            'title': list,             
            'content': list,
            'title_clean': list,
            'content_clean': list,
            'title_abbreviation': list,
            'content_abbreviation': list,
            'title_entity': list,
            'content_entity': list,
            'title_stopword_removed': list,
            'content_stopword_removed': list,
            'title_stemmed': list,
            'content_stemmed': list,
            'full_text': list,
            'input_ids': list,     
            'attention_mask': list,
            'sentiment_label': list,
            'sentiment_score': list,
            'embedding': list          
        })
        grouped_news['emb_mean'] = grouped_news['embedding'].apply(lambda emb_list: np.mean(np.stack(emb_list), axis=0) if len(emb_list) > 0 else None)
        grouped_news['positive_grouped_news_sentiment'] = grouped_news['sentiment_label'].apply(lambda labels: labels.count('POSITIVE') if labels else 0)
        grouped_news['negative_grouped_news_sentiment'] = grouped_news['sentiment_label'].apply(lambda labels: labels.count('NEGATIVE') if labels else 0)
        grouped_news['mean_sentiment_score_positive'] = grouped_news.apply(lambda new: self.mean_sentiment_score(new, 'POSITIVE'), axis=1)
        grouped_news['mean_sentiment_score_negative'] = grouped_news.apply(lambda new: self.mean_sentiment_score(new, 'NEGATIVE'), axis=1)

        return grouped_news
    
    def __load_pca(self, stock_name):
        try:
            self.scaler = joblib.load(f"data/Models/{stock_name}/scaler.joblib")
            self.pca = joblib.load(f"data/Models/{stock_name}/pca.joblib")
            return True
        except FileNotFoundError:
            self.scaler = StandardScaler()
            self.pca = PCA(n_components=50, random_state=0)
            return False
    
    def normalization_data(self, news, stock_name = "", fit = False):
        x_emb = np.vstack(news['emb_mean'].values)
        if fit:
            x_scaled = self.scaler.fit_transform(x_emb)
            x_pca = self.pca.fit_transform(x_scaled)
            os.makedirs(f"data/Models/{stock_name}", exist_ok=True)
            joblib.dump(self.scaler, f"data/Models/{stock_name}/scaler.joblib")
            joblib.dump(self.pca, f"data/Models/{stock_name}/pca.joblib")
        else:
            x_scaled = self.scaler.transform(x_emb)
            x_pca = self.pca.transform(x_scaled)

        for i in range(50):
            news[f'sentiment_pca_{i}'] = x_pca[:, i]
        
        return news