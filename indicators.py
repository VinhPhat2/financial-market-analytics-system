# indicators.py
import pandas as pd
import numpy as np

def rma(series, period):
    return series.ewm(alpha=1/period, adjust=False, min_periods=period).mean()

def compute_rsi_matrix(close_df, period=14):
    delta = close_df.diff()
    rs = rma(delta.clip(lower=0), period) / rma(-delta.clip(upper=0), period)
    return 100 - (100 / (1 + rs))

def calculate_all_indicators(p_high, p_low, p_close, wr_len, stoch_len):
    wpr = (p_close - p_high.rolling(wr_len).max()) / (p_high.rolling(wr_len).max() - p_low.rolling(wr_len).min()) * 100 
    
    rsi_8 = compute_rsi_matrix(p_close, stoch_len)
    rsi_14 = compute_rsi_matrix(p_close, 14)
    stoch_k = ((rsi_8 - rsi_8.rolling(stoch_len).min()) / (rsi_8.rolling(stoch_len).max() - rsi_8.rolling(stoch_len).min()) * 100).rolling(3).mean()
    
    tr = pd.DataFrame(np.maximum(p_high - p_low, np.maximum((p_high - p_close.shift(1)).abs(), (p_low - p_close.shift(1)).abs())))
    atr_14 = rma(tr, 14)
    
    return wpr, stoch_k, atr_14, rsi_14

def analyze_vni_regime(vni_close):
    vni_now = vni_close.iloc[-1]
    vni_sma20 = vni_close.rolling(20).mean().iloc[-1]
    vni_sma50 = vni_close.rolling(50).mean().iloc[-1]
    
    vni_prev = vni_close.iloc[-2] if len(vni_close) > 1 else vni_now
    vni_change = vni_now - vni_prev
    vni_pct = (vni_change / vni_prev) * 100 if vni_prev else 0
    vni_str = f"{vni_now:,.2f} ({'+' if vni_change > 0 else ''}{vni_change:,.2f} | {'+' if vni_pct > 0 else ''}{vni_pct:.2f}%)"
    
    if vni_now > vni_sma20 and vni_now > vni_sma50: regime = "UPTREND"
    elif vni_now < vni_sma20 and vni_now < vni_sma50: regime = "DOWNTREND"
    else: regime = "SIDEWAY"
    return vni_str, regime

def analyze_market_breadth(p_close, latest_date):
    today_c = p_close.loc[latest_date]
    advancers = decliners = unchanged = 0
    if len(p_close) >= 2:
        prev_c_all = p_close.iloc[-2]
        advancers = (today_c > prev_c_all).sum()
        decliners = (today_c < prev_c_all).sum()
        unchanged = (today_c == prev_c_all).sum()
    
    valid_counts = today_c.notna().sum()
    pct_ma20 = (today_c > p_close.rolling(20).mean().loc[latest_date]).sum() / valid_counts * 100 if valid_counts > 0 else 0
    pct_ma50 = (today_c > p_close.rolling(50).mean().loc[latest_date]).sum() / valid_counts * 100 if valid_counts > 0 else 0
    
    if pct_ma20 < 20: breadth_status = "🧊 Hoảng loạn tột độ (Cơ hội)"
    elif pct_ma20 < 40: breadth_status = "📉 Dòng tiền chưa mạnh"
    elif pct_ma20 < 60: breadth_status = "⚖️ Đi ngang giằng co"
    elif pct_ma20 < 80: breadth_status = "📈 Sóng tăng lan tỏa"
    else: breadth_status = "🔥 Hưng phấn / FOMO (Rủi ro)"

    breadth_str = f"🟢 {advancers} Tăng | 🔴 {decliners} Giảm\n**Trạng thái ngắn hạn:** {pct_ma20:.1f}% mã > MA20 ➔ **{breadth_status}**\n**Trạng thái trung hạn:** {pct_ma50:.1f}% mã > MA50"
    return breadth_str, advancers, decliners, unchanged, pct_ma20, pct_ma50

def filter_buy_signals(wpr, stoch_k, can_trade):
    return ((wpr.rolling(3).min() <= -75) | (stoch_k.rolling(3).min() <= 25)) & can_trade