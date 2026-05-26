# config.py

# ============================================================
#   CONFIGURATIONS & PARAMETERS (PHOENIX: T+ APEX)
# ============================================================

# --- DISCORD ---
DISCORD_WEBHOOK_URL = ""

# --- VNSTOCK API KEY ---
VNSTOCK_API_KEY = ""

# --- FILE LƯU TRẠNG THÁI BOT ---
PORTFOLIO_FILE      = "portfolio_BATDAY.json"
SL_HISTORY_FILE     = "sl_history.json"
SIGNAL_HISTORY_FILE = "signal_history.json"
TRADE_STATS_FILE    = "trade_stats.json"

# --- ĐƯỜNG DẪN DỮ LIỆU ---
DATA_FOLDER = r""

# --- QUẢN TRỊ DANH MỤC & VỐN ---
MAX_PORTFOLIO_SIZE   = 50
MAX_SIGNAL_PER_DAY   = 3
MIN_GTGD             = 4_080_000_000
MIN_PRICE            = 9.0
SIGNAL_COOLDOWN_BARS = 3

# --- CẤU HÌNH KỸ THUẬT ---
WR_LEN, STOCH_LEN = 10, 8
ATR_SL_MULT       = 1.52
ATR_TP1_MULT      = 2.44
ATR_TP_MULT       = 4.66
MAX_HOLD          = 10

# --- SYSTEM THROTTLING ---
GLOBAL_MIN_INTERVAL = 1.5