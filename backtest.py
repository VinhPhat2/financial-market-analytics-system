import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================================
#   CONFIGURATIONS 
# ============================================================
DATA_FOLDER = r"E:\hoctap\NLP\Dữ liệu chứng khoán"
FILE_NAME   = "WHITELIST_stocks_history_only.csv"

# Quản trị vốn 
INITIAL_CAPITAL      = 1_000_000_000  
MAX_PORTFOLIO_SIZE   = 5      
MAX_SIGNAL_PER_DAY   = 5      
MIN_GTGD             = 4_080_000_000    
MIN_PRICE            = 9.0              
SIGNAL_COOLDOWN_BARS = 3     

# Chi phí & Trượt giá
FEE_RATE             = 0.001 
TAX_RATE             = 0.001 
SLIPPAGE_PCT         = 0.001 

# Tham số Kỹ thuật
WR_LEN, STOCH_LEN = 10, 8
ATR_SL_MULT       = 1.52    
ATR_TP1_MULT      = 2.44    # Nấc 1
ATR_TP_MULT       = 4.66   # Nấc 2
MAX_HOLD          = 10    

# Tham số Backtest
START_DATE               = "2026-01-04"  
END_DATE                 = "2026-05-20"  

# Vốn cơ sở
BASE_POSITION_PCT = 0.18  

class Colors:
    HEADER, BLUE, GREEN = '\033[95m', '\033[94m', '\033[92m'  
    WARNING, FAIL, ENDC, BOLD = '\033[93m', '\033[91m', '\033[0m', '\033[1m'

def rma(series, period):
    return series.ewm(alpha=1/period, adjust=False, min_periods=period).mean()

def compute_rsi_matrix(close_df, period=14):
    delta = close_df.diff()
    rs = rma(delta.clip(lower=0), period) / rma(-delta.clip(upper=0), period)
    return 100 - (100 / (1 + rs))

def run_backtest():
    print(f"{Colors.HEADER}>> INITIALIZING PHOENIX ENGINE (PURE SCALE-OUT + EQUITY DRAWDOWN SIZING)...{Colors.ENDC}")
    
    # 1. LOAD DATA
    print(">> Đang nạp dữ liệu lịch sử...")
    df_prices = pd.read_csv(os.path.join(DATA_FOLDER, FILE_NAME))
    rename_map = {"Ngày": "time", "Lần cuối": "close", "KL": "volume", "Mở": "open", "Cao": "high", "Thấp": "low"}
    if 'time' not in df_prices.columns: df_prices.rename(columns=rename_map, inplace=True)
    
    df_prices["time"] = pd.to_datetime(df_prices["time"], dayfirst=False, errors='coerce')
    df_prices.dropna(subset=['time'], inplace=True)
    
    for col in ["close", "open", "high", "low", "volume"]:
        if df_prices[col].dtype == object:
            df_prices[col] = df_prices[col].astype(str).str.replace(',', '').astype(float)
            
    df_prices = df_prices.sort_values(['symbol', 'time']).drop_duplicates(subset=['symbol', 'time'], keep='last')

    p_close = df_prices.pivot(index="time", columns="symbol", values="close")
    p_vol = df_prices.pivot(index="time", columns="symbol", values="volume").fillna(0)
    p_high = df_prices.pivot(index="time", columns="symbol", values="high")
    p_open = df_prices.pivot(index="time", columns="symbol", values="open")
    p_low = df_prices.pivot(index="time", columns="symbol", values="low")

    # Chỉ dùng để định giá portfolio nếu một mã bị thiếu close ở ngày nào đó
    p_close_val = p_close.ffill()

    # 2. INDICATORS 
    print(">> Đang tính toán ma trận chỉ báo...")
    wpr = (p_close - p_high.rolling(WR_LEN).max()) / (p_high.rolling(WR_LEN).max() - p_low.rolling(WR_LEN).min()) * 100 
    rsi_8 = compute_rsi_matrix(p_close, STOCH_LEN)
    stoch_k = ((rsi_8 - rsi_8.rolling(STOCH_LEN).min()) / (rsi_8.rolling(STOCH_LEN).max() - rsi_8.rolling(STOCH_LEN).min()) * 100).rolling(3).mean()
    
    tr = pd.DataFrame(np.maximum(p_high - p_low, np.maximum((p_high - p_close.shift(1)).abs(), (p_low - p_close.shift(1)).abs())))
    atr_14 = rma(tr, 14)
    momentum_20 = p_close.pct_change(20)

    # --- STRATEGY LOGIC ---
    # Tín hiệu mua thuần túy dựa trên các nhịp nhúng sâu của WPR và StochRSI
    buy_signals = (wpr.rolling(3).min() <= -75) | (stoch_k.rolling(3).min() <= 25)

    # 3. SIMULATION LOOP
    print(">> Đang chạy Walk-forward mô phỏng giao dịch...")
    portfolio = {}  
    trade_log = []
    daily_capital = []
    cash = INITIAL_CAPITAL
    
    cumulative_max_equity = INITIAL_CAPITAL
    
    start_dt = pd.to_datetime(START_DATE)
    end_dt = pd.to_datetime(END_DATE)
    dates = p_close.index[(p_close.index >= start_dt) & (p_close.index <= end_dt)].tolist()
    
    sl_history = {} 
    signal_history = {} 

    for i, date in enumerate(dates):
        today_c, today_h, today_l, today_o = p_close.loc[date], p_high.loc[date], p_low.loc[date], p_open.loc[date]
        today_v = p_vol.loc[date]
        today_val_c = p_close_val.loc[date]
        sold_today = set()
        
        current_equity = cash + sum([
            pos['shares'] * today_val_c[sym] 
            for sym, pos in portfolio.items() 
            if sym in today_val_c.index and not pd.isna(today_val_c[sym])
        ])
        
        cumulative_max_equity = max(cumulative_max_equity, current_equity)
        current_dd = (current_equity / cumulative_max_equity) - 1
        
        # =========================================================================
        # A. SMART EXIT LOGIC
        # =========================================================================
        to_remove = []
        for sym, pos in portfolio.items():
            if pd.isna(today_c[sym]): continue
            
            cp, ch, cl, co = today_c[sym], today_h[sym], today_l[sym], today_o[sym]
            ep, tp1, tp2, sl = pos['entry_price'], pos['tp1_price'], pos['target_price'], pos['dynamic_sl']
            bars_held = i - pos['entry_idx']
            current_atr = atr_14.loc[date, sym]
            
            pos['highest_c'] = max(pos['highest_c'], cp)
            if pos['highest_c'] >= ep + (2.5 * current_atr) and not pos['tp1_hit']:
                safe_sl = ep * (1 + (FEE_RATE*2) + TAX_RATE + (SLIPPAGE_PCT*2) + 0.01)
                if pos['dynamic_sl'] < safe_sl:
                    pos['dynamic_sl'] = safe_sl
                    sl = pos['dynamic_sl']
            
            exit_price = None
            reason = ""
            can_sell = bars_held >= 2 
            
            if can_sell:
                if not pos['tp1_hit'] and ch >= tp1:
                    sell_shares = pos['shares'] // 2  
                    if sell_shares > 0:
                        exit_price_half = tp1 * (1 - SLIPPAGE_PCT)
                        gross_rev = sell_shares * exit_price_half
                        net_rev = gross_rev * (1 - FEE_RATE - TAX_RATE)
                        
                        cost_basis = (pos['total_cost'] / pos['shares']) * sell_shares
                        profit = net_rev - cost_basis
                        pnl_pct = profit / cost_basis if cost_basis > 0 else 0
                        
                        cash += net_rev
                        pos['shares'] -= sell_shares
                        pos['total_cost'] -= cost_basis
                        pos['tp1_hit'] = True
                        
                        safe_sl = ep * (1 + (FEE_RATE*2) + TAX_RATE + (SLIPPAGE_PCT*2))
                        if pos['dynamic_sl'] < safe_sl:
                            pos['dynamic_sl'] = safe_sl
                            sl = pos['dynamic_sl']
                        
                        trade_log.append({
                            'Entry_Date': pos['entry_date'], 'Exit_Date': date, 'Symbol': sym,
                            'Entry_Price': ep, 'Exit_Price': exit_price_half,
                            'PnL_Pct': pnl_pct, 'Profit_VND': profit, 'Reason': f"Chốt Lời 1/2 (TP {ATR_TP1_MULT} ATR) 🎯", 'Bars_Held': bars_held
                        })

                if bars_held == 2:
                    if cp <= sl:
                        exit_price = cp * (1 - SLIPPAGE_PCT)
                        reason = "Cắt Lỗ EOD (Chạm SL cứng) 🔴"
                    elif cp >= tp2:
                        exit_price = cp * (1 - SLIPPAGE_PCT)
                        reason = "Chốt Lời MAX EOD 🚀"

                elif bars_held > 2:
                    if cl <= sl:
                        exit_price = sl * (1 - SLIPPAGE_PCT)
                        if sl >= ep:
                            reason = "Khóa Lãi Intraday (Mid-way Protect) 🛡️"
                        else:
                            reason = "Cắt Lỗ Intraday 🔴"
                            
                    elif ch >= tp2:
                        exit_price = tp2 * (1 - SLIPPAGE_PCT)
                        reason = f"Chốt Lời MAX (TP {ATR_TP_MULT} ATR) 🚀"
                    
                    elif bars_held >= MAX_HOLD:
                        if cp < ep + (0.5 * current_atr):
                            exit_price = cp * (1 - SLIPPAGE_PCT)
                            reason = "Time Stop (Cơ cấu mã yếu) ⏰"

            if exit_price is not None:
                gross_revenue = pos['shares'] * exit_price
                sell_fee = gross_revenue * FEE_RATE
                tax = gross_revenue * TAX_RATE
                net_revenue = gross_revenue - sell_fee - tax
                
                total_cost = pos['total_cost'] 
                profit = net_revenue - total_cost
                pnl_pct = profit / total_cost 
                
                cash += net_revenue
                
                trade_log.append({
                    'Entry_Date': pos['entry_date'], 'Exit_Date': date, 'Symbol': sym,
                    'Entry_Price': ep, 'Exit_Price': exit_price,
                    'PnL_Pct': pnl_pct, 'Profit_VND': profit, 'Reason': reason, 'Bars_Held': bars_held
                })
                to_remove.append(sym)
                sold_today.add(sym)
                if "Lỗ" in reason or "Time Stop" in reason: sl_history[sym] = i

        for sym in to_remove: del portfolio[sym]
            
        # =========================================================================
        # B. XỬ LÝ MUA LỆNH MỚI
        # =========================================================================
        room_left = MAX_PORTFOLIO_SIZE - len(portfolio)
        if room_left > 0:
            raw_buy = buy_signals.loc[date][buy_signals.loc[date]].index.tolist()
            valid_cands = []
            
            for sym in raw_buy:
                if sym in portfolio or sym in sold_today: continue
                last_sl_idx = sl_history.get(sym, -999)
                last_sig_idx = signal_history.get(sym, -999)
                
                if (i - last_sl_idx >= SIGNAL_COOLDOWN_BARS) and (i - last_sig_idx >= SIGNAL_COOLDOWN_BARS):
                    turnover = today_c[sym] * today_v[sym] * 1000
                    if turnover >= MIN_GTGD and today_c[sym] >= MIN_PRICE:
                        valid_cands.append({'sym': sym, 'stoch_k': stoch_k.loc[date, sym], 'momentum': momentum_20.loc[date, sym]})
            
            sorted_cands = sorted(valid_cands, key=lambda x: x['stoch_k'])
            
            if current_dd < -0.10:
                dynamic_base_pct = BASE_POSITION_PCT * 0.7 
            elif current_dd < -0.05:
                dynamic_base_pct = BASE_POSITION_PCT * 0.75 
            else:
                dynamic_base_pct = BASE_POSITION_PCT        
                
            for cand in sorted_cands[:min(MAX_SIGNAL_PER_DAY, room_left)]:
                sym = cand['sym']
                current_atr = atr_14.loc[date, sym]
                ep = today_c[sym]
                ep_actual = ep * (1 + SLIPPAGE_PCT)
                
                base_alloc = current_equity * dynamic_base_pct
                strength_multiplier = max(0.8, min(1.0 + cand['momentum'], 1.2)) 
                trade_alloc = base_alloc * strength_multiplier
                
                max_capital_allowed = current_equity * 0.18
                if trade_alloc > max_capital_allowed:
                    trade_alloc = max_capital_allowed
                
                trade_alloc = min(trade_alloc, cash) 
                
                if trade_alloc >= ep_actual:
                    shares = int(trade_alloc / (ep_actual * (1 + FEE_RATE))) 
                    if shares > 0:
                        cost = shares * ep_actual
                        buy_fee = cost * FEE_RATE
                        total_cost = cost + buy_fee 
                        
                        cash -= total_cost
                        
                        portfolio[sym] = {
                            'shares': shares, 
                            'entry_price': ep_actual, 
                            'entry_date': date,
                            'total_cost': total_cost, 
                            'tp1_price': ep_actual + (ATR_TP1_MULT * current_atr),
                            'target_price': ep_actual + (ATR_TP_MULT * current_atr),
                            'stop_loss_price': ep_actual - (ATR_SL_MULT * current_atr),
                            'dynamic_sl': ep_actual - (ATR_SL_MULT * current_atr), 
                            'highest_c': ep_actual, 
                            'entry_idx': i,
                            'tp1_hit': False 
                        }
                        signal_history[sym] = i

        port_value = cash + sum([
            pos['shares'] * p_close_val.loc[date, sym] 
            for sym, pos in portfolio.items() 
            if sym in p_close_val.columns and not pd.isna(p_close_val.loc[date, sym])
        ])
        daily_capital.append({'Date': date, 'Equity': port_value})

    # 4. TÍNH TOÁN QUANTS METRICS
    print(">> Đang tổng hợp Metrics...")
    if not daily_capital: return

    df_trades = pd.DataFrame(trade_log)
    df_equity = pd.DataFrame(daily_capital).set_index('Date')
    
    if df_trades.empty:
        print("❌ Cảnh báo: Không có giao dịch nào được thực hiện.")
        return

    df_equity['Daily_Return'] = df_equity['Equity'].pct_change()
    total_return = (df_equity['Equity'].iloc[-1] / INITIAL_CAPITAL) - 1
    
    days = (df_equity.index[-1] - df_equity.index[0]).days
    annualized_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
    sharpe_ratio = np.sqrt(252) * (df_equity['Daily_Return'].mean() / df_equity['Daily_Return'].std())
    
    cumulative_max = df_equity['Equity'].cummax()
    drawdown = (df_equity['Equity'] / cumulative_max) - 1
    max_drawdown = drawdown.min()
    
    total_trades = len(df_trades)
    wins = df_trades[df_trades['PnL_Pct'] > 0]
    losses = df_trades[df_trades['PnL_Pct'] <= 0]
    
    win_rate = len(wins) / total_trades if total_trades > 0 else 0
    avg_win = wins['PnL_Pct'].mean() if not wins.empty else 0
    avg_loss = losses['PnL_Pct'].mean() if not losses.empty else 0
    profit_factor = abs(wins['Profit_VND'].sum() / losses['Profit_VND'].sum()) if not losses.empty and losses['Profit_VND'].sum() != 0 else float('inf')

    # 5. IN BÁO CÁO (REPORT)
    print(f"\n{Colors.HEADER}========================================================================{Colors.ENDC}")
    print(f"{Colors.HEADER}    PHOENIX APEX - EQUITY CURVE TRADING (DD SIZING REDUCTION)           {Colors.ENDC}")
    print(f"{Colors.HEADER}========================================================================{Colors.ENDC}")
    print(f"Giai đoạn Backtest : {df_equity.index[0].strftime('%Y-%m-%d')} đến {df_equity.index[-1].strftime('%Y-%m-%d')} ({days} ngày)")
    print(f"Vốn ban đầu        : {INITIAL_CAPITAL:,.0f} VNĐ")
    print(f"Giá trị cuối kỳ    : {df_equity['Equity'].iloc[-1]:,.0f} VNĐ")
    print(f"------------------------------------------------------------------------")
    print(f"Return Tổng        : {Colors.GREEN if total_return > 0 else Colors.FAIL}{total_return:.2%}{Colors.ENDC}")
    print(f"Sharpe Ratio       : {Colors.BOLD}{sharpe_ratio:.2f}{Colors.ENDC}")
    print(f"Max Drawdown       : {Colors.FAIL}{max_drawdown:.2%}{Colors.ENDC}")
    print(f"------------------------------------------------------------------------")
    print(f"Tổng số lệnh (N)   : {total_trades} lệnh")
    print(f"Win Rate           : {Colors.BOLD}{win_rate:.2%}{Colors.ENDC}")
    print(f"Avg Net Win/Loss   : {avg_win:.2%} / {avg_loss:.2%}")
    print(f"\n[THỐNG KÊ LÝ DO CHỐT LỆNH]")
    print(df_trades['Reason'].value_counts().to_string())
    print(f"{Colors.HEADER}========================================================================{Colors.ENDC}")

    # 6. VISUALIZATION
    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [2, 1]})
    
    axes[0].plot(df_equity.index, df_equity['Equity'], color='cyan', linewidth=1.5)
    axes[0].fill_between(df_equity.index, df_equity['Equity'], df_equity['Equity'].min(), color='cyan', alpha=0.1)
    axes[0].set_title(f'Phoenix Strategy Equity Curve (Sharpe: {sharpe_ratio:.2f} | Max DD: {max_drawdown:.2%})', fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Portfolio Value (VNĐ)', fontsize=12)
    axes[0].grid(color='gray', linestyle='--', alpha=0.3)

    sns.histplot(df_trades['PnL_Pct'] * 100, bins=50, kde=True, ax=axes[1], color='dodgerblue')
    axes[1].axvline(0, color='red', linestyle='dashed', linewidth=1.5)
    axes[1].axvline(df_trades['PnL_Pct'].mean() * 100, color='lime', linestyle='dashed', linewidth=1.5, label='Mean Net PnL')
    axes[1].set_title('Trade Net PnL (%) Distribution (Slippage & Fees applied)', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Net Profit / Loss (%)', fontsize=12)
    axes[1].set_ylabel('Number of Trades', fontsize=12)
    axes[1].legend()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_backtest()