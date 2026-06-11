import yfinance as yf
import argparse
import pandas as pd
import numpy as np
import joblib
from tensorflow.keras.models import load_model
from datetime import date, datetime

loaded_model = load_model('model_saham_lstm.keras')
loaded_scaler_X = joblib.load('scaler_X.joblib')
loaded_scaler_y = joblib.load('scaler_y.joblib')
loaded_selected_features = joblib.load('selected_features.joblib')
lookback = 25
print("Model dan komponen berhasil dimuat.")

def predict_new_stock(ticker, lookback, df_func):
    last_sequence_raw = df_func[loaded_selected_features].iloc[-lookback:].values
    last_sequence_scaled = loaded_scaler_X.transform(last_sequence_raw)
    X_input = last_sequence_scaled.reshape(1, lookback, len(loaded_selected_features))
    pred_scaled = loaded_model.predict(X_input)
    pred_price = loaded_scaler_y.inverse_transform(pred_scaled)[0, 0]
    
    return pred_price

def preprocess_data(df):
    df = df[df['Close'] > 0]
    df = df[df['Volume'] > 0]
    df['Return'] = df['Close'].pct_change()
    df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA100'] = df['Close'].rolling(100).mean()
    df['Price_MA5_Ratio'] = df['Close'] / df['MA5']
    df['Price_MA10_Ratio'] = df['Close'] / df['MA10']
    df['Price_MA20_Ratio'] = df['Close'] / df['MA20']
    df['Price_MA50_Ratio'] = df['Close'] / df['MA50']
    df['Price_MA100_Ratio'] = df['Close'] / df['MA100']
    df['Volatility'] = df['Return'].rolling(5).std()
    df['Momentum'] = df['Close'] - df['Close'].shift(5)
    df['Volume_Change'] = df['Volume'].pct_change()

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['Return'] = df['Return'].clip(-0.1, 0.1)

    df['Target_Close'] = df['Close'].shift(-1)

    df = df.dropna()

    return df

def download_data(kode_saham):
    df = yf.download(kode_saham, start="2018-01-01", end="2026-05-01")
    df.columns = df.columns.droplevel(1)
    df.columns.name = None
    df = df.reset_index()
    df.to_csv(f"{kode_saham}.csv")

parser = argparse.ArgumentParser(description="Download data saham dari Yahoo Finance")
parser.add_argument("--saham", type=str, required=True, help="Kode saham (contoh: BBCA, TLKM, ASII)")
args = parser.parse_args()

kode = args.saham.strip().upper()
if not kode:
    print("Kode saham tidak boleh kosong.")
else:
    download_data(f"{kode}.JK")
    df = pd.read_csv(f'{kode}.JK.csv')
    df = df.drop(columns=['Unnamed: 0'])
    df = preprocess_data(df)
    X_full = df[loaded_selected_features].values
    X_scaled = loaded_scaler_X.transform(X_full)
    X_seq = []
    for i in range(lookback, len(X_scaled)):
        X_seq.append(X_scaled[i-lookback:i])
    X_seq = np.array(X_seq)
    y_pred_full = loaded_model.predict(X_seq, verbose=0)
    y_pred_price = loaded_scaler_y.inverse_transform(y_pred_full)
    last_pred = y_pred_price[-1][0]
    predict = predict_new_stock(kode, lookback, df)
    now = datetime.now()
    print(f"Prediksi dilakukan pada: {now.strftime("%Y-%m-%d %H:%M:%S")}")
    print(f"Prediksi: {round(predict, 0) - round(last_pred, 0)}")
