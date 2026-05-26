# data_engine.py
import os
import time
import sys
import re
import random
import logging
import pandas as pd
from datetime import datetime, timedelta
from utils import _parse_special_format
from config import GLOBAL_MIN_INTERVAL, DATA_FOLDER, VNSTOCK_API_KEY

# Nạp API key trước khi import vnstock
os.environ["VNSTOCK_API_KEY"] = VNSTOCK_API_KEY
os.environ["VNSTOCK_API_TOKEN"] = VNSTOCK_API_KEY
os.environ["VNSTOCK_KEY"] = VNSTOCK_API_KEY

logging.getLogger('vnstock').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

import warnings
warnings.filterwarnings('ignore')

try:
    from vnstock import Quote
except ImportError:
    print("❌ Error: Vui lòng cài đặt vnstock.")
    sys.exit()

_last_tick = 0.0

def global_throttle():
    global _last_tick
    now = time.monotonic()
    dt = now - _last_tick
    if dt < GLOBAL_MIN_INTERVAL:
        time.sleep(GLOBAL_MIN_INTERVAL - dt)
    _last_tick = time.monotonic()

def parse_wait(s, default=30):
    m = re.search(r'(?:sau|after)\s+(\d+)\s*(?:giây|seconds?)', s, flags=re.I)
    if m: return max(int(m.group(1)), 1)
    m2 = re.search(r'(\d+)', s)
    return max(int(m2.group(1)), 1) if m2 else default

def get_candle_targeted(symbol):
    symbol = str(symbol).upper().strip()

    end_str = datetime.now().strftime('%Y-%m-%d')
    start_str = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')

    max_attempts = 5
    backoff = 5
    backoff_max = 120
    
    for attempt in range(max_attempts):
        try:
            global_throttle()
            q = Quote(symbol=symbol, source="VCI")
            df = q.history(start=start_str, end=end_str, interval='1D')
            
            if df is not None and not df.empty:
                df.columns = [c.lower() for c in df.columns]

                if 'date' in df.columns:
                    df = df.rename(columns={'date': 'time'})

                if 'ticker' in df.columns:
                    df = df.rename(columns={'ticker': 'symbol'})

                if 'symbol' not in df.columns:
                    df['symbol'] = symbol
                
                df['time'] = pd.to_datetime(df['time'], errors='coerce')

                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                df = df.dropna(subset=['time', 'close'])
                df = df.sort_values('time')

                if not df.empty:
                    return df[['time', 'symbol', 'open', 'high', 'low', 'close', 'volume']].tail(1).reset_index(drop=True)

            break 

        except KeyboardInterrupt:
            raise

        except SystemExit:
            return None

        except Exception as e:
            if attempt < max_attempts - 1:
                msg = str(e).lower()
                wait_time = max(parse_wait(msg), backoff) + random.uniform(1, 3)
                time.sleep(wait_time)
                backoff = min(backoff * 2, backoff_max) 
            else:
                pass

    return None

def load_historical_data():
    df_prices_hist = pd.read_csv(os.path.join(DATA_FOLDER, "WHITELIST_stocks_history_only.csv"))
    df_vnindex_hist = pd.read_csv(os.path.join(DATA_FOLDER, "Dữ liệu Lịch sử VN Index.csv"))
    
    rename_map = {
        "Ngày": "time",
        "Lần cuối": "close",
        "KL": "volume",
        "Mở": "open",
        "Cao": "high",
        "Thấp": "low"
    }

    df_vnindex_hist.rename(columns=rename_map, inplace=True)

    if 'date' in df_prices_hist.columns and 'time' not in df_prices_hist.columns:
        df_prices_hist.rename(columns={'date': 'time'}, inplace=True)

    if 'ticker' in df_prices_hist.columns and 'symbol' not in df_prices_hist.columns:
        df_prices_hist.rename(columns={'ticker': 'symbol'}, inplace=True)

    if 'time' not in df_prices_hist.columns:
        df_prices_hist.rename(columns=rename_map, inplace=True)

    for col in ["close", "open", "high", "low", "volume"]:
        if col in df_vnindex_hist.columns: 
            df_vnindex_hist[col] = df_vnindex_hist[col].apply(_parse_special_format)

    for df in (df_prices_hist, df_vnindex_hist):
        df["time"] = pd.to_datetime(df["time"], dayfirst=False, errors='coerce')
        df.dropna(subset=['time'], inplace=True)

    for col in ["close", "open", "high", "low", "volume"]:
        if col in df_prices_hist.columns:
            df_prices_hist[col] = pd.to_numeric(df_prices_hist[col], errors='coerce')
        if col in df_vnindex_hist.columns:
            df_vnindex_hist[col] = pd.to_numeric(df_vnindex_hist[col], errors='coerce')

    cutoff = pd.Timestamp.now() - pd.DateOffset(years=3)
    df_vnindex_hist = df_vnindex_hist[df_vnindex_hist['time'] >= cutoff]
    df_prices_hist = df_prices_hist[df_prices_hist['time'] >= cutoff]

    df_prices_hist = df_prices_hist.sort_values(['symbol', 'time']).drop_duplicates(subset=['symbol', 'time'], keep='last')
    df_vnindex_hist = df_vnindex_hist.sort_values('time').drop_duplicates(subset=['time'], keep='last')

    whitelist_symbols = df_prices_hist['symbol'].unique().tolist()
    
    return df_prices_hist, df_vnindex_hist, whitelist_symbols