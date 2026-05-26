# portfolio_engine.py
from distutils import cygwinccompiler
import pandas as pd
from config import *
from utils import update_portfolio_buy

def process_exits(portfolio, p_close, today_c, today_h, today_l, atr_14, latest_date, current_time_str, now, trade_stats, sl_history):
    sell_msgs, to_remove = [], []
    for sym, info in portfolio.items():
        if sym not in today_c.index or pd.isna(today_c[sym]): continue
        cp, ch, cl = today_c[sym], today_h[sym], today_l[sym]
        
        ep = info['entry_price']
        ed = pd.to_datetime(info['entry_date'])
        bars_held = len(p_close.loc[ed:latest_date]) - 1
        current_atr = atr_14.loc[latest_date, sym]
        
        if pd.isna(current_atr) or current_atr <= 0:
            continue
        
        tp1 = info.get('tp1_price', ep + (ATR_TP1_MULT * current_atr))
        tp2 = info.get('target_price', ep + (ATR_TP_MULT * current_atr))
        current_sl = info.get('dynamic_sl', info.get('stop_loss_price'))
        
        info['highest_c'] = max(info.get('highest_c', ep), cp)
        
        if info['highest_c'] >= ep + (2.5 * current_atr) and not info.get('tp1_hit', False):
            safe_sl = ep * 1.005 
            if current_sl < safe_sl:
                info['dynamic_sl'] = safe_sl
                current_sl = safe_sl
        
        can_sell = (bars_held > 2) or (bars_held == 2 and now.hour >= 13)
        is_end_of_day = (now.hour == 14 and now.minute >= 20) or (now.hour >= 15)
        full_exit, reason, exit_price = False, "", None

        if can_sell:
            if not info.get('tp1_hit', False) and ch >= tp1:
                info['tp1_hit'] = True
                safe_sl = ep * 1.004
                if info.get('dynamic_sl', current_sl) < safe_sl: info['dynamic_sl'] = safe_sl
                
                pnl_pct = (tp1 - ep) / ep
                sell_msgs.append({
                    "Thời Gian": current_time_str, "Symbol": sym, 
                    "Current_Price": f"{tp1:,.1f}", "Entry_Price": f"{ep:,.1f}", 
                    "PnL": f"{pnl_pct:.2%}", "Action": f"Chốt Lời 1/2 (TP1 {ATR_TP1_MULT} ATR) 🎯"
                })
                trade_stats['wins'] += 1 

            if bars_held == 2:
                if cp <= current_sl and is_end_of_day: full_exit, exit_price, reason = True, cp, "Cắt Lỗ EOD (Chạm SL) 🔴"
                elif cp >= tp2 and is_end_of_day: full_exit, exit_price, reason = True, cp, "Chốt Lời MAX EOD 🚀"
            elif bars_held > 2:
                if cl <= current_sl: full_exit, exit_price, reason = True, current_sl, "Khóa Lãi / Cắt Lỗ Intraday 🛡️"
                elif ch >= tp2: full_exit, exit_price, reason = True, tp2, f"Chốt Lời MAX (TP2 {ATR_TP_MULT} ATR) 🚀"
                elif bars_held >= MAX_HOLD and is_end_of_day:
                    if cp < ep + (0.5 * current_atr): full_exit, exit_price, reason = True, cp, "Time Stop (Cơ cấu mã yếu) ⏰"

        if full_exit:
            pnl_pct = (exit_price - ep) / ep
            sell_msgs.append({
                "Thời Gian": current_time_str, "Symbol": sym, 
                "Current_Price": f"{exit_price:,.1f}", "Entry_Price": f"{ep:,.1f}", 
                "PnL": f"{pnl_pct:.2%}", "Action": reason
            })
            to_remove.append(sym)
            if exit_price > ep: trade_stats['wins'] += 1
            else: trade_stats['losses'] += 1
            if "Lỗ" in reason or "Time Stop" in reason: sl_history[sym] = latest_date.strftime('%Y-%m-%d')

    for sym in to_remove: portfolio.pop(sym, None)
    return portfolio, sell_msgs, to_remove, trade_stats, sl_history

def process_buys(buy_signals, portfolio, p_close, p_vol, today_c, wpr, stoch_k, rsi_14, atr_14, latest_date, current_time_str, signal_history, sl_history, sent_tickers_today, sold_tickers_today):
    room_left = MAX_PORTFOLIO_SIZE - len(portfolio)
    raw_buy = buy_signals.loc[latest_date][buy_signals.loc[latest_date]].index.tolist()
    valid_cands = []
    
    for sym in [s for s in raw_buy if s not in sold_tickers_today and s not in portfolio]:
        sig_date = pd.to_datetime(signal_history.get(sym, '2000-01-01'))
        bars_passed = len(p_close.loc[sig_date:latest_date])-1 if sig_date in p_close.index else (latest_date - sig_date).days
        if bars_passed >= SIGNAL_COOLDOWN_BARS:
            price = today_c.get(sym, pd.NA)
            volume = p_vol.loc[latest_date, sym] if sym in p_vol.columns else pd.NA

            if pd.isna(price) or pd.isna(volume):
                continue

            turnover = price * volume * 1000

            if turnover >= MIN_GTGD and price >= MIN_PRICE:
                valid_cands.append({
                    'sym': sym,
                    'stoch_k': stoch_k.loc[latest_date, sym],
                    'wpr': wpr.loc[latest_date, sym],
                    'rsi': rsi_14.loc[latest_date, sym]
                })
    discord_buy, results = [], []
    sorted_cands = sorted(valid_cands, key=lambda x: x['stoch_k'])
    
    for i, cand in enumerate(sorted_cands[:MAX_SIGNAL_PER_DAY]):
        sym = cand['sym']
        if sym in sent_tickers_today: continue
        signal_history[sym] = latest_date.strftime('%Y-%m-%d')
        
        priority_tag = "🔥 [TOP 1 ƯU TIÊN]" if i == 0 else ("⭐ [TOP 2]" if i == 1 else "✅")
        current_atr = atr_14.loc[latest_date, sym]
        if pd.isna(current_atr) or current_atr <= 0:
            continue
        
        dynamic_sl = today_c[sym] - (ATR_SL_MULT * current_atr)
        tp1_price = today_c[sym] + (ATR_TP1_MULT * current_atr)
        tp2_price = today_c[sym] + (ATR_TP_MULT * current_atr)
        
        status = "❌ Hết Room" if room_left <= 0 else "✅ Đã Vào Danh Mục"
        if room_left > 0: 
            portfolio = update_portfolio_buy(portfolio, sym, today_c[sym], tp1_price, tp2_price, dynamic_sl, latest_date.strftime('%Y-%m-%d'))
            room_left -= 1
        
        item = {
            "Thời Gian": current_time_str, "Mã": f"{priority_tag} {sym}",  
            "Giá Mua": f"{today_c[sym]:,.1f}", 
            "Mục Tiêu": f"TP1: {tp1_price:,.1f} | TP2: {tp2_price:,.1f}", 
            "Cắt Lỗ": f"{dynamic_sl:,.1f}", "GTGD": "Chờ quét", 
            "Chỉ Báo (W/S/R)": f"{cand['wpr']:.0f} / {cand['stoch_k']:.0f} / {cand['rsi']:.1f}", 
            "Trạng Thái": status
        }
        results.append(item); discord_buy.append(item); sent_tickers_today.add(sym)

    return portfolio, results, discord_buy, signal_history, sent_tickers_today, room_left