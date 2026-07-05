"""
analyzer.py — Tính toán indicators từ DataFrame nến:
    EMA9, EMA21, RSI(14), MACD(12,26,9), ATR(14)
"""

import pandas as pd
import ta

from logger_setup import get_logger

log = get_logger("analyzer")


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Thêm các cột indicator vào DataFrame nến.
    Yêu cầu: df phải có cột 'close', 'high', 'low'.
    Trả về df đã bổ sung cột indicator.
    """
    if df is None or len(df) < 30:
        log.warning("DataFrame quá ít nến (%d) để tính indicators",
                    0 if df is None else len(df))
        return df

    close = df["close"]
    high  = df["high"]
    low   = df["low"]

    # EMA
    df["ema9"]  = ta.trend.EMAIndicator(close, window=9).ema_indicator()
    df["ema21"] = ta.trend.EMAIndicator(close, window=21).ema_indicator()

    # RSI
    df["rsi"] = ta.momentum.RSIIndicator(close, window=14).rsi()

    # MACD
    macd_obj      = ta.trend.MACD(close, window_fast=12, window_slow=26, window_sign=9)
    df["macd"]    = macd_obj.macd()
    df["macd_sig"] = macd_obj.macd_signal()
    df["macd_hist"] = macd_obj.macd_diff()

    # ATR (dự phòng, không dùng cho lot nhưng hữu ích để debug)
    df["atr"] = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range()

    return df


def get_last_row(df: pd.DataFrame) -> pd.Series | None:
    """
    Trả về nến gần nhất đã đóng (index -2).
    Index -1 là nến đang hình thành — KHÔNG dùng để ra tín hiệu.
    """
    if df is None or len(df) < 3:
        return None
    return df.iloc[-2]


def get_prev_row(df: pd.DataFrame) -> pd.Series | None:
    """Trả về nến trước nến gần nhất đã đóng (index -3). Dùng để detect crossover."""
    if df is None or len(df) < 4:
        return None
    return df.iloc[-3]
