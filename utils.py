# utils.py
import os
import sys
import json
import pandas as pd
import numpy as np

class Colors:
    HEADER, BLUE, GREEN = '\033[95m', '\033[94m', '\033[92m'  
    WARNING, FAIL, ENDC, BOLD = '\033[93m', '\033[91m', '\033[0m', '\033[1m'

def clear_console(): 
    os.system('cls' if os.name == 'nt' else 'clear')

def beep_alert():
    if os.name == 'nt':
        try: import winsound; winsound.Beep(1000, 500) 
        except: pass
    else: sys.stdout.write('\a')

def _parse_special_format(x):
    if not isinstance(x, str) and pd.isna(x): return np.nan
    if isinstance(x, str):
        x = x.strip().upper()
        mult = 1.0
        if 'M' in x: mult = 1e6; x = x.replace('M', '')
        elif 'K' in x: mult = 1e3; x = x.replace('K', '')
        elif 'B' in x: mult = 1e9; x = x.replace('B', '')
        elif '%' in x: mult = 0.01; x = x.replace('%', '')
        try: return float(x.replace(",", "")) * mult
        except ValueError: return np.nan
    return float(x)

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {}

def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def update_portfolio_buy(portfolio, symbol, entry_price, tp1_price, target_price, stop_loss_price, date_str):
    if symbol not in portfolio:
        portfolio[symbol] = {
            "entry_price": entry_price, 
            "entry_date": date_str, 
            "tp1_price": tp1_price,
            "target_price": target_price,
            "stop_loss_price": stop_loss_price,
            "dynamic_sl": stop_loss_price,  
            "highest_c": entry_price,       
            "tp1_hit": False                
        }
    return portfolio