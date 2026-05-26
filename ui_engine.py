# ui_engine.py
import pandas as pd
from utils import Colors, clear_console, beep_alert
from config import MAX_PORTFOLIO_SIZE

def render_dashboard(latest_date, vni_str, vni_color, vni_regime, advancers, decliners, unchanged, pct_ma20, pct_ma50, trade_stats, portfolio, room_left, sell_msgs, results, raw_buy):
    clear_console()
    print(f"{Colors.HEADER}========================================================================{Colors.ENDC}")
    print(f"{Colors.HEADER}  BOT UEHER ĐI HỌC: {latest_date.strftime('%d/%m/%Y')}   {Colors.ENDC}")
    print(f"{Colors.HEADER}========================================================================{Colors.ENDC}")
    print(f">> VN-Index: {vni_str} | Trạng thái: {vni_color}{vni_regime}{Colors.ENDC}")
    print(f">> Độ rộng: 🟢 {advancers} Tăng | 🔴 {decliners} Giảm | 🟡 {unchanged} TC")
    
    ma20_color = Colors.FAIL if pct_ma20 < 20 else (Colors.GREEN if pct_ma20 > 80 else Colors.BLUE)
    ma50_color = Colors.FAIL if pct_ma50 < 20 else (Colors.GREEN if pct_ma50 > 80 else Colors.BLUE)
    print(f">> Dòng tiền: {ma20_color}{pct_ma20:.1f}%{Colors.ENDC} mã > MA20 | {ma50_color}{pct_ma50:.1f}%{Colors.ENDC} mã > MA50")
    
    total_trades = trade_stats.get('wins', 0) + trade_stats.get('losses', 0)
    win_rate = (trade_stats.get('wins', 0) / total_trades * 100) if total_trades > 0 else 0
    print(f">> Lịch sử Giao dịch: Đã đóng {total_trades} lệnh | Win Rate: {Colors.BOLD}{win_rate:.1f}%{Colors.ENDC}")
    print(f"{Colors.HEADER}------------------------------------------------------------------------{Colors.ENDC}")
    print(f">> Quản trị danh mục: Cầm {len(portfolio)}/{MAX_PORTFOLIO_SIZE} mã. (Room trống: {room_left})")
    
    print(f"\n{Colors.WARNING}>> TÍN HIỆU BÁN (Bao gồm Scale-out 1/2):{Colors.ENDC}")
    print(pd.DataFrame(sell_msgs)[['Thời Gian', 'Symbol', 'Current_Price', 'PnL', 'Action']].to_markdown(index=False) if sell_msgs else "  Chưa có tín hiệu thoát lệnh.")

    if results:
        print(f"\n{Colors.GREEN}>> TÍN HIỆU MUA ({len(results)} mã):{Colors.ENDC}"); beep_alert()
        print(pd.DataFrame(results)[['Thời Gian', 'Mã', 'Giá Mua', 'Cắt Lỗ', 'Trạng Thái', 'Mục Tiêu', 'Chỉ Báo (W/S/R)']].to_markdown(index=False))
    elif raw_buy:
        print(f"\n{Colors.BLUE}>> Có tín hiệu chạm mốc nhưng bị lọc (GTGD < 4 Tỷ / Giá < 9k / Đã phím).{Colors.ENDC}")
    else:
        print(f"\n{Colors.BLUE}>> Không có setup bắt đáy nào thỏa mãn.{Colors.ENDC}")