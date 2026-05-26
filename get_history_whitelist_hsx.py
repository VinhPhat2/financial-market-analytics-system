import os

# =====================================================
# API KEY - ĐẶT TRƯỚC KHI IMPORT VNSTOCK
# =====================================================
VNSTOCK_API_KEY = ""

os.environ["VNSTOCK_API_KEY"] = VNSTOCK_API_KEY
os.environ["VNSTOCK_API_TOKEN"] = VNSTOCK_API_KEY
os.environ["VNSTOCK_KEY"] = VNSTOCK_API_KEY

print("Đã nạp API key trong code.")
print("Có API key:", bool(os.getenv("VNSTOCK_API_KEY")))
print("Độ dài key:", len(os.getenv("VNSTOCK_API_KEY", "")))

import re
import time
import random
import pandas as pd
from datetime import date
from tqdm import tqdm
from vnstock import Listing, Quote


# =====================================================
# CẤU HÌNH
# =====================================================
FOLDER_PATH = r"E:\hoctap\NLP\Dữ liệu chứng khoán"
FILE_NAME = "WHITELIST_stocks_history_only.csv"
FULL_PATH = os.path.join(FOLDER_PATH, FILE_NAME)

START = "2015-01-01"
END = date.today().isoformat()

DATA_SOURCE = "VCI"

# True = xóa file cũ rồi tải lại sạch từ đầu
# False = nếu file đã có mã nào rồi thì bỏ qua mã đó
CLEAR_OLD_FILE = False

BATCH = 25
MAX_ATTEMPTS = 3
GLOBAL_MIN_INTERVAL = 1.2
BACKOFF_MAX = 60

_last_tick = 0.0


# =====================================================
# CHỈ TẢI ĐÚNG CÁC MÃ TRONG LIST NÀY
# =====================================================
TICKERS_WHITELIST = [
    "AAA","AAM","AAT","ABR","ABS","ABT","ACB","ACC","ACG","ACL","ADG","ADP","ADS",
    "AGG","AGR","ANV","APG","APH","ASG","ASM","ASP","AST","BAF","BBC","BCE","BCG",
    "BCM","BFC","BHN","BIC","BID","BKG","BMC","BMI","BMP","BRC","BSI","BSR","BTP",
    "BTT","BVH","BWE","C32","C47","CCC","CCI","CCL","CDC","CHP","CIG","CII","CKG",
    "CLC","CLL","CLW","CMG","CMV","CMX","CNG","COM","CRC","CRE","CRV","CSM","CSV",
    "CTD","CTF","CTG","CTI","CTR","CTS","CVT","D2D","DAH","DAT","DBC","DBD","DBT",
    "DC4","DCL","DCM","DGC","DGW","DHA","DHC","DHG","DHM","DIG","DLG","DMC","DPG",
    "DPM","DPR","DQC","DRC","DRH","DRL","DSC","DSE","DSN","DTA","DTL","DTT","DVP",
    "DXG","DXS","DXV","EIB","ELC","EVE","EVF","EVG","FCM","FCN","FDC","FIR","FIT",
    "FMC","FPT","FRT","FTS","GAS","GDT","GEE","GEG","GEX","GIL","GMD","GMH","GSP",
    "GTA","GVR","HAG","HAH","HAP","HAR","HAS","HAX","HCD","HCM","HDB","HDC","HDG",
    "HHP","HHS","HHV","HID","HII","HMC","HNA","HPG","HPX","HQC","HRC","HSG","HSL",
    "HT1","HTG","HTI","HTL","HTN","HTV","HU1","HUB","HVH","HVN","HVX","ICT","IDI",
    "IJC","ILB","IMP","ITC","ITD","JVC","KBC","KDC","KDH","KHG","KHP","KMR","KOS",
    "KSB","L10","LAF","LBM","LCG","LDG","LGC","LGL","LHG","LIX","LM8","LPB","LSS",
    "MBB","MCM","MCP","MDG","MHC","MIG","MSB","MSH","MSN","MWG","NAB","NAF","NAV",
    "NBB","NCT","NHA","NHH","NHT","NKG","NLG","NNC","NO1","NSC","NT2","NTC","NTL",
    "NVL","NVT","OCB","OGC","OPC","ORS","PAC","PAN","PC1","PDN","PDR","PDV","PET",
    "PGC","PGD","PGI","PGV","PHC","PHR","PIT","PJT","PLP","PLX","PMG","PNC","PNJ",
    "POW","PPC","PTB","PTC","PTL","PVD","PVP","PVT","QCG","QNP","RAL","REE","RYG",
    "S4A","SAB","SAM","SAV","SBA","SBG","SBT","SBV","SC5","SCR","SCS","SFC","SFG",
    "SFI","SGN","SGR","SGT","SHA","SHB","SHI","SHP","SIP","SJD","SJS","SKG","SMA",
    "SMB","SMC","SPM","SRC","SRF","SSB","SSC","SSI","ST8","STB","STG","STK","SVC",
    "SVD","SVI","SVT","SZC","SZL","TAL","TBC","TCB","TCD","TCH","TCI","TCL","TCM",
    "TCO","TCR","TCT","TCX","TDC","TDG","TDH","TDM","TDP","TDW","TEG","THG","TIP",
    "TIX","TLD","TLG","TLH","TMP","TMS","TMT","TN1","TNC","TNH","TNI","TNT","TPB",
    "TPC","TRA","TRC","TSC","TTA","TTE","TTF","TV2","TVB","TVS","TVT","TYA","UIC",
    "VAB","VAF","VCA","VCB","VCF","VCG","VCI","VDP","VDS","VFG","VGC","VHC","VHM",
    "VIB","VIC","VID","VIP","VIX","VJC","VMD","VND","VNE","VNG","VNL","VNM","VNS",
    "VOS","VPB","VPD","VPG","VPH","VPI","VPL","VPS","VRC","VRE","VSC","VSH","VSI",
    "VTB","VTO","VTP","YBM","YEG"
]


# =====================================================
# HÀM PHỤ TRỢ
# =====================================================
def clean_ticker_list(tickers):
    cleaned = []
    seen = set()

    for ticker in tickers:
        symbol = str(ticker).upper().strip()

        if not symbol:
            continue

        if symbol not in seen:
            cleaned.append(symbol)
            seen.add(symbol)

    return cleaned


def global_throttle():
    global _last_tick

    now = time.monotonic()
    dt = now - _last_tick

    if dt < GLOBAL_MIN_INTERVAL:
        time.sleep(GLOBAL_MIN_INTERVAL - dt)

    _last_tick = time.monotonic()


def parse_wait(error_message, default=30):
    text = str(error_message)

    m = re.search(r"(?:sau|after)\s+(\d+)\s*(?:giây|seconds?)", text, flags=re.I)
    if m:
        return max(int(m.group(1)), 1)

    m2 = re.search(r"(\d+)", text)
    if m2:
        return max(int(m2.group(1)), 1)

    return default


def get_downloaded_symbols():
    if not os.path.exists(FULL_PATH) or os.path.getsize(FULL_PATH) == 0:
        return set()

    try:
        old = pd.read_csv(FULL_PATH, usecols=["symbol"])
        return set(old["symbol"].astype(str).str.upper().str.strip().unique())
    except Exception as e:
        print(f"Không đọc được file cũ để resume: {e}")
        return set()


def clean_price_df(df_one, symbol):
    if df_one is None or df_one.empty:
        return None

    df = df_one.copy()

    if "date" in df.columns and "time" not in df.columns:
        df = df.rename(columns={"date": "time"})

    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")
        df = df[df["time"] >= pd.to_datetime(START)]
        df = df.sort_values("time")

    if df.empty:
        return None

    df["symbol"] = symbol

    cols = ["symbol"] + [c for c in df.columns if c != "symbol"]
    df = df[cols]

    return df


def download_one_symbol(symbol):
    q = Quote(symbol=symbol, source=DATA_SOURCE)
    df_one = q.history(start=START, end=END)
    return clean_price_df(df_one, symbol)


def save_data(batch_buffer):
    if not batch_buffer:
        return

    try:
        df_batch = pd.concat(batch_buffer, ignore_index=True)

        if "time" in df_batch.columns:
            df_batch["time"] = pd.to_datetime(df_batch["time"], errors="coerce")
            df_batch = df_batch.sort_values(["symbol", "time"])

        file_exists = os.path.exists(FULL_PATH) and os.path.getsize(FULL_PATH) > 0

        df_batch.to_csv(
            FULL_PATH,
            mode="a",
            header=not file_exists,
            index=False,
            encoding="utf-8-sig"
        )

        print(f"Đã lưu thêm {df_batch['symbol'].nunique()} mã | {len(df_batch):,} dòng")

    except Exception as e:
        print(f"Lỗi khi lưu dữ liệu: {e}")


def save_failed_symbols(failed_symbols):
    if not failed_symbols:
        return

    failed_path = os.path.join(FOLDER_PATH, "failed_symbols_only_whitelist.csv")
    df_failed = pd.DataFrame(failed_symbols, columns=["symbol", "error"])
    df_failed.to_csv(failed_path, index=False, encoding="utf-8-sig")

    print(f"Đã lưu danh sách mã lỗi tại: {failed_path}")


def test_one_symbol():
    print("Đang test tải FPT...")

    df = download_one_symbol("FPT")

    if df is None or df.empty:
        print("Không tải được FPT.")
        return

    print(df.head())
    print(df.tail())
    print(df.shape)


# =====================================================
# CHƯƠNG TRÌNH CHÍNH
# =====================================================
def main():
    os.makedirs(FOLDER_PATH, exist_ok=True)

    tickers = clean_ticker_list(TICKERS_WHITELIST)

    print("=" * 70)
    print("BẮT ĐẦU TẢI DỮ LIỆU")
    print(f"Nguồn dữ liệu: {DATA_SOURCE}")
    print(f"Từ ngày: {START}")
    print(f"Đến ngày: {END}")
    print(f"Số mã trong whitelist: {len(tickers)}")
    print(f"File lưu: {FULL_PATH}")
    print("=" * 70)

    if CLEAR_OLD_FILE and os.path.exists(FULL_PATH):
        os.remove(FULL_PATH)
        print("Đã xóa file cũ để tải lại sạch từ đầu.")

    downloaded_symbols = get_downloaded_symbols()

    tickers_to_download = [
        symbol for symbol in tickers
        if symbol not in downloaded_symbols
    ]

    print(f"Đã có trong file: {len(downloaded_symbols)} mã")
    print(f"Còn cần tải: {len(tickers_to_download)} mã")
    print("=" * 70)

    if not tickers_to_download:
        print("Không còn mã nào cần tải.")
        return

    batch_buffer = []
    successful = 0
    failed_symbols = []

    progress = tqdm(tickers_to_download, desc="Tiến độ", unit="mã")

    for symbol in progress:
        attempts = 0
        backoff = 8

        while attempts < MAX_ATTEMPTS:
            attempts += 1

            try:
                global_throttle()

                df_one = download_one_symbol(symbol)

                if df_one is not None and not df_one.empty:
                    batch_buffer.append(df_one)
                    successful += 1
                    progress.set_description(f"OK {symbol}")
                else:
                    failed_symbols.append((symbol, "empty_data"))
                    progress.write(f"[{symbol}] Không có dữ liệu.")

                break

            except KeyboardInterrupt:
                print("\nBạn đã bấm dừng chương trình.")
                print("Đang lưu dữ liệu đã tải được...")
                save_data(batch_buffer)
                save_failed_symbols(failed_symbols)
                return

            except SystemExit as e:
                print("\nVnstock/thư viện tự dừng.")
                print(f"Lý do: {repr(e)}")
                print("Đang lưu dữ liệu đã tải được...")
                save_data(batch_buffer)
                save_failed_symbols(failed_symbols)
                return

            except Exception as e:
                msg = str(e).lower()

                is_rate_limit = any(
                    key in msg
                    for key in [
                        "rate limit",
                        "thử lại sau",
                        "too many",
                        "blocked",
                        "429",
                        "timeout",
                        "temporarily"
                    ]
                )

                if is_rate_limit and attempts < MAX_ATTEMPTS:
                    wait_time = min(max(parse_wait(msg), backoff), BACKOFF_MAX)
                    wait_time = wait_time + random.uniform(1, 3)

                    progress.set_description(f"[{symbol}] Nghỉ {wait_time:.1f}s")
                    time.sleep(wait_time)

                    backoff = min(backoff * 2, BACKOFF_MAX)

                else:
                    error_text = repr(e)
                    failed_symbols.append((symbol, error_text))
                    progress.write(f"[{symbol}] Lỗi sau {attempts} lần thử: {error_text}")
                    break

        if len(batch_buffer) >= BATCH:
            save_data(batch_buffer)
            batch_buffer = []

        # Nghỉ rất nhẹ, không quét sàn, không nghỉ lâu
        if successful > 0 and successful % 80 == 0:
            sleep_time = random.uniform(5, 10)
            progress.set_description(f"Nghỉ nhẹ {sleep_time:.1f}s")
            time.sleep(sleep_time)

    if batch_buffer:
        save_data(batch_buffer)

    save_failed_symbols(failed_symbols)

    print("\n" + "=" * 70)
    print("HOÀN TẤT")
    print(f"Tải thành công thêm: {successful} mã")
    print(f"Lỗi/không có dữ liệu: {len(failed_symbols)} mã")
    print(f"File dữ liệu: {FULL_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    # Nếu muốn test trước thì mở dòng này:
    # test_one_symbol()

    main()