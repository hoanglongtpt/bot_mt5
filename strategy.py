"""
strategy.py — Logic phát hiện tín hiệu BUY / SELL / None

Điều kiện BUY (tất cả phải thỏa mãn):
  1. EMA9 vừa cắt lên trên EMA21 (crossover tại nến đã đóng gần nhất)
  2. RSI nằm trong khoảng [40, 65]  — tránh overbought
  3. MACD histogram dương (momentum tăng)

Điều kiện SELL (tất cả phải thỏa mãn):
  1. EMA9 vừa cắt xuống dưới EMA21 (crossover tại nến đã đóng gần nhất)
  2. RSI nằm trong khoảng [35, 60]  — tránh oversold
  3. MACD histogram âm (momentum giảm)

Tín hiệu chỉ được lấy từ nến ĐÃ ĐÓNG — tránh repaint.
"""

import pandas as pd

from logger_setup import get_logger
from analyzer import get_last_row, get_prev_row

log = get_logger("strategy")

# Ngưỡng RSI
RSI_BUY_MIN  = 40
RSI_BUY_MAX  = 65
RSI_SELL_MIN = 35
RSI_SELL_MAX = 60


def detect_signal(df: pd.DataFrame) -> str | None:
    """
    Phân tích df (đã có indicators) và trả về:
        "BUY"  — tín hiệu mua
        "SELL" — tín hiệu bán
        None   — không có tín hiệu
    """
    cur  = get_last_row(df)   # nến vừa đóng
    prev = get_prev_row(df)   # nến trước đó

    if cur is None or prev is None:
        log.debug("Không đủ dữ liệu để detect signal")
        return None

    # Kiểm tra NaN
    required = ["ema9", "ema21", "rsi", "macd_hist"]
    for col in required:
        if pd.isna(cur[col]) or pd.isna(prev[col]):
            log.debug("Indicator %s chứa NaN — bỏ qua", col)
            return None

    ema9_cur   = cur["ema9"]
    ema21_cur  = cur["ema21"]
    ema9_prev  = prev["ema9"]
    ema21_prev = prev["ema21"]
    rsi        = cur["rsi"]
    macd_hist  = cur["macd_hist"]

    # ── BUY ──────────────────────────────────────────────────────────
    ema_cross_up = (ema9_prev <= ema21_prev) and (ema9_cur > ema21_cur)
    rsi_ok_buy   = RSI_BUY_MIN <= rsi <= RSI_BUY_MAX
    macd_bull    = macd_hist > 0

    if ema_cross_up and rsi_ok_buy and macd_bull:
        log.info("Tín hiệu BUY — EMA cross up | RSI=%.1f | MACD_hist=%.5f",
                 rsi, macd_hist)
        return "BUY"

    # ── SELL ─────────────────────────────────────────────────────────
    ema_cross_dn  = (ema9_prev >= ema21_prev) and (ema9_cur < ema21_cur)
    rsi_ok_sell   = RSI_SELL_MIN <= rsi <= RSI_SELL_MAX
    macd_bear     = macd_hist < 0

    if ema_cross_dn and rsi_ok_sell and macd_bear:
        log.info("Tín hiệu SELL — EMA cross dn | RSI=%.1f | MACD_hist=%.5f",
                 rsi, macd_hist)
        return "SELL"

    log.debug("Không có tín hiệu | EMA9=%.5f EMA21=%.5f RSI=%.1f MACD_hist=%.5f",
              ema9_cur, ema21_cur, rsi, macd_hist)
    return None
