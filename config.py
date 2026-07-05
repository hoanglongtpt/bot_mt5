"""
config.py — Toàn bộ cấu hình bot MT5
Chỉnh sửa file này để thay đổi symbol, SL/TP, credentials, v.v.
"""

import os
from dotenv import load_dotenv
import MetaTrader5 as mt5

load_dotenv()

# ─────────────────────────────────────────
# MT5 ACCOUNT (điền vào .env hoặc trực tiếp)
# ─────────────────────────────────────────
MT5_LOGIN    = int(os.getenv("MT5_LOGIN", "0"))        # số tài khoản
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")           # mật khẩu
MT5_SERVER   = os.getenv("MT5_SERVER", "")             # tên server broker

# ─────────────────────────────────────────
# SYMBOL & TIMEFRAME
# ─────────────────────────────────────────
SYMBOL     = "EURUSDm"          # cặp tiền giao dịch (sửa theo broker)
TIMEFRAME  = mt5.TIMEFRAME_M5   # khung nến M5
CANDLES    = 100                # số nến lấy để phân tích

# ─────────────────────────────────────────
# LỆNH
# ─────────────────────────────────────────
LOT_SIZE   = 0.01   # lot cố định
TP_USD     = 2.0    # take profit tính theo USD
SL_USD     = 1.0    # stop loss tính theo USD

# ─────────────────────────────────────────
# RISK MANAGEMENT
# ─────────────────────────────────────────
MAX_OPEN_ORDERS = 2   # tối đa 2 lệnh cùng lúc

# ─────────────────────────────────────────
# VÒNG LẶP
# ─────────────────────────────────────────
LOOP_SLEEP_SECONDS = 10   # kiểm tra mỗi 10 giây

# ─────────────────────────────────────────
# MAGIC NUMBER (định danh lệnh của bot)
# ─────────────────────────────────────────
MAGIC = 202601
