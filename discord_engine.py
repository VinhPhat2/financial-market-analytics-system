# discord_engine.py
import requests
import time
from datetime import datetime
from config import DISCORD_WEBHOOK_URL, MAX_PORTFOLIO_SIZE
from utils import Colors

def send_discord_alert(buy_data, sell_data, vni_str, vni_regime, room_left, breadth_str):
    if not buy_data and not sell_data: return
    
    embed_fields = []
    for item in sell_data:
        icon = "🟢" if not "-" in item['PnL'] else "🔴"
        if "Time Stop" in item['Action']: icon = "⏰"
        
        embed_fields.append({
            "name": f"{icon} BÁN: {item['Symbol']} | ⏱️ {item['Thời Gian']}", 
            "value": f"**Giá Bán:** {item['Current_Price']} (Vốn: {item['Entry_Price']})\n**Biến động:** {item['PnL']} -> **{item['Action']}**", 
            "inline": False
        })

    for item in buy_data:
        embed_fields.append({
            "name": f"⚡ BẮT ĐÁY: {item['Mã']} | ⏱️ {item['Thời Gian']}", 
            "value": f"**Trạng thái:** {item['Trạng Thái']}\n**Mua:** {item['Giá Mua']}\n**Target:** {item['Mục Tiêu']} | **Cắt lỗ:** {item['Cắt Lỗ']}\n**Vol:** {item['GTGD']} | **WPR/Stoch/RSI:** {item['Chỉ Báo (W/S/R)']}", 
            "inline": False
        })

    embed_color = 5763719 if vni_regime == "UPTREND" else (16753920 if vni_regime == "SIDEWAY" else 15548997)
    chunks = [embed_fields[i:i + 20] for i in range(0, len(embed_fields), 20)]

    for chunk in chunks:
        payload = {
            "username": "Phoenix Engine",
            "embeds": [{
                "title": f"PHOENIX APEX | Danh mục: {MAX_PORTFOLIO_SIZE - room_left}/{MAX_PORTFOLIO_SIZE} mã",
                "description": f"**VN-INDEX:** {vni_str} ({vni_regime})\n**Dòng tiền:** {breadth_str}",
                "color": embed_color, "fields": chunk
            }]
        }
        if DISCORD_WEBHOOK_URL:
            try: requests.post(DISCORD_WEBHOOK_URL, json=payload)
            except Exception as e: print(f"[{Colors.FAIL}Network Error{Colors.ENDC}] Lỗi Discord: {e}")
            time.sleep(1) 

def send_eod_summary(sent_tickers, portfolio, vni_str):
    desc = f"Hôm nay đã phím **{len(sent_tickers)} mã**: {', '.join(sent_tickers)}" if sent_tickers else "Hôm nay không có tín hiệu đạt chuẩn."
    payload = {
        "username": "Phoenix Engine",
        "embeds": [{
            "title": f"📊 TỔNG KẾT CUỐI NGÀY | {datetime.now().strftime('%d/%m/%Y')}",
            "description": desc, "color": 3447003,
            "fields": [
                {"name": "VN-Index", "value": f"{vni_str}", "inline": True},
                {"name": "Danh Mục", "value": f"Nắm giữ {len(portfolio)}/{MAX_PORTFOLIO_SIZE} mã.", "inline": True}
            ]
        }]
    }
    if DISCORD_WEBHOOK_URL:
        try: 
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
            print(f"\n{Colors.GREEN}>> ĐÃ GỬI BÁO CÁO CUỐI NGÀY LÊN DISCORD.{Colors.ENDC}")
        except: pass