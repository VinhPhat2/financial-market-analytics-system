# main.py
import os
import sys
import time
import pandas as pd
from datetime import datetime

# (Microservices)
from config import *
from utils import Colors, load_json, save_json
import data_engine
import indicators
import portfolio_engine
import ui_engine
import discord_engine

def run_realtime_dashboard():
    print(f"{Colors.HEADER}>> INITIALIZING PHOENIX ENGINE (CLEAN ARCHITECTURE)...{Colors.ENDC}")
    
    try:
        df_prices_hist, df_vnindex_hist, whitelist_symbols = data_engine.load_historical_data()
        print(f">> DATA LOADED. WATCHLIST: {len(whitelist_symbols)} ASSETS.")
    except Exception as e: 
        print(f"❌ Initialization Error: {e}"); return

    time.sleep(1)
    sent_tickers_today, sold_tickers_today = set(), set()
    last_reset_day = datetime.now().day
    eod_summary_sent = False 

    while True:
        try:
            now = datetime.now()
            if now.day != last_reset_day:
                sent_tickers_today.clear(); sold_tickers_today.clear()
                last_reset_day, eod_summary_sent = now.day, False
                print(f"\n>> NEW TRADING SESSION. CACHE CLEARED.")

            print(f"\n🔄 DATA SCAN IN PROGRESS... ({now.strftime('%H:%M:%S')})")
            
            portfolio = load_json(PORTFOLIO_FILE)
            sl_history = load_json(SL_HISTORY_FILE)
            signal_history = load_json(SIGNAL_HISTORY_FILE)
            trade_stats = load_json(TRADE_STATS_FILE) or {"wins": 0, "losses": 0}

            new_rows = []
            processed_count = 0
            for sym in whitelist_symbols:
                data = data_engine.get_candle_targeted(sym) 
                if data is not None: new_rows.append(data)
                processed_count += 1
                sys.stdout.write(f"\r>> Progress: {processed_count}/{len(whitelist_symbols)} [VCI] ")
                sys.stdout.flush()
                
            if not new_rows: 
                print(f"\n{Colors.WARNING}>> Dữ liệu trống. Thử lại sau 60s...{Colors.ENDC}"); time.sleep(60); continue
            
            sys.stdout.write(f"\n>> Fetching VN-INDEX... ") 
            vni_row = next((data_engine.get_candle_targeted('VNINDEX') for _ in range(5) if data_engine.get_candle_targeted('VNINDEX') is not None), None)
            print(f"{Colors.GREEN}OK{Colors.ENDC}" if vni_row is not None else f"{Colors.FAIL}FAILED{Colors.ENDC}")
            
            today_date = pd.to_datetime(now.date())
            df_full = pd.concat([df_prices_hist[df_prices_hist['time'] < today_date], pd.concat(new_rows)], ignore_index=True)
            df_full = df_full.sort_values(['symbol', 'time']).drop_duplicates(subset=['symbol', 'time'], keep='last')
            
            df_vni_full = pd.concat([df_vnindex_hist[df_vnindex_hist['time'] < today_date]] + ([vni_row] if vni_row is not None else []), ignore_index=True)
            vni_close = df_vni_full.sort_values("time").drop_duplicates(subset=['time'], keep='last')['close'].astype(float)
            
            p_close = df_full.pivot(index="time", columns="symbol", values="close")
            p_vol = df_full.pivot(index="time", columns="symbol", values="volume")
            p_high = df_full.pivot(index="time", columns="symbol", values="high")
            p_low = df_full.pivot(index="time", columns="symbol", values="low")
            
            latest_date, current_time_str = p_close.index[-1], now.strftime('%H:%M:%S')
            today_c, today_h, today_l = p_close.loc[latest_date], p_high.loc[latest_date], p_low.loc[latest_date]
            
            vni_str, vni_regime = indicators.analyze_vni_regime(vni_close)
            vni_color = Colors.GREEN if vni_regime == "UPTREND" else (Colors.FAIL if vni_regime == "DOWNTREND" else Colors.WARNING)
            
            wpr, stoch_k, atr_14, rsi_14 = indicators.calculate_all_indicators(p_high, p_low, p_close, WR_LEN, STOCH_LEN)
            breadth_str, advancers, decliners, unchanged, pct_ma20, pct_ma50 = indicators.analyze_market_breadth(p_close, latest_date)
            
            can_trade = pd.Series(True, index=p_close.columns)
            for sym, sl_date in sl_history.items():
                if len(p_close.loc[pd.to_datetime(sl_date):latest_date]) - 1 < 3: can_trade[sym] = False
            
            buy_signals = indicators.filter_buy_signals(wpr, stoch_k, can_trade)
            raw_buy = buy_signals.loc[latest_date][buy_signals.loc[latest_date]].index.tolist()

            portfolio, sell_msgs, sold_tickers, trade_stats, sl_history = portfolio_engine.process_exits(
                portfolio, p_close, today_c, today_h, today_l, atr_14, latest_date, current_time_str, now, trade_stats, sl_history
            )
            sold_tickers_today.update(sold_tickers)

            portfolio, results, discord_buy, signal_history, sent_tickers_today, room_left = portfolio_engine.process_buys(
                buy_signals, portfolio, p_close, p_vol, today_c, wpr, stoch_k, rsi_14, atr_14, latest_date, current_time_str, signal_history, sl_history, sent_tickers_today, sold_tickers_today
            )

            save_json(portfolio, PORTFOLIO_FILE); save_json(sl_history, SL_HISTORY_FILE)
            save_json(trade_stats, TRADE_STATS_FILE); save_json(signal_history, SIGNAL_HISTORY_FILE)

            ui_engine.render_dashboard(latest_date, vni_str, vni_color, vni_regime, advancers, decliners, unchanged, pct_ma20, pct_ma50, trade_stats, portfolio, room_left, sell_msgs, results, raw_buy)
            discord_engine.send_discord_alert(discord_buy, sell_msgs, vni_str, vni_regime, room_left, breadth_str)
            
            if now.hour >= 15 and not eod_summary_sent:
                discord_engine.send_eod_summary([sym for sym, date_str in signal_history.items() if date_str == now.strftime('%Y-%m-%d')], portfolio, vni_str)
                eod_summary_sent = True

            print(f"\n>> Nghỉ 60s...")
            time.sleep(60)

        except KeyboardInterrupt: 
            print("\n>> Execution Terminated."); break
        except Exception as e: 
            print(f"❌ Cycle Error: {e}"); time.sleep(10)

if __name__ == "__main__":
    run_realtime_dashboard()