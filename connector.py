"""
connector.py — Kết nối MT5, lấy dữ liệu nến và thông tin symbol
"""

import time
import pandas as pd
import MetaTrader5 as mt5

from logger_setup import get_logger
import config

log = get_logger("connector")


def connect() -> bool:
    """Khởi tạo kết nối và đăng nhập MT5."""
    if not mt5.initialize():
        log.error("mt5.initialize() thất bại: %s", mt5.last_error())
        return False

    if config.MT5_LOGIN and config.MT5_PASSWORD and config.MT5_SERVER:
        ok = mt5.login(
            login=config.MT5_LOGIN,
            password=config.MT5_PASSWORD,
            server=config.MT5_SERVER
        )
        if not ok:
            log.error("Đăng nhập MT5 thất bại: %s", mt5.last_error())
            mt5.shutdown()
            return False
        log.info("Đăng nhập thành công — account #%s", config.MT5_LOGIN)
    else:
        log.info("Dùng phiên đang đăng nhập sẵn trong MT5 terminal")

    info = mt5.account_info()
    if info is None:
        log.error("Không lấy được account_info: %s", mt5.last_error())
        return False

    log.info("Account: %s | Server: %s | Balance: %.2f %s",
             info.login, info.server, info.balance, info.currency)
    return True


def disconnect() -> None:
    mt5.shutdown()
    log.info("Đã ngắt kết nối MT5")


def ensure_connected() -> bool:
    """Kiểm tra kết nối còn sống, tự reconnect nếu cần."""
    if mt5.account_info() is not None:
        return True
    log.warning("Mất kết nối MT5 — đang thử reconnect...")
    for attempt in range(1, 6):
        time.sleep(5 * attempt)
        if connect():
            log.info("Reconnect thành công (lần %d)", attempt)
            return True
        log.warning("Reconnect lần %d thất bại", attempt)
    log.error("Không thể reconnect sau 5 lần thử")
    return False


def get_candles(symbol: str, timeframe: int, n: int) -> pd.DataFrame | None:
    """Lấy n nến gần nhất, trả về DataFrame với cột OHLCV + time."""
    if not ensure_connected():
        return None

    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    if rates is None or len(rates) == 0:
        log.error("copy_rates_from_pos thất bại cho %s: %s", symbol, mt5.last_error())
        return None

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    return df


def get_symbol_info(symbol: str) -> mt5.SymbolInfo | None:
    """Lấy thông tin symbol (pip value, digits, v.v.)"""
    info = mt5.symbol_info(symbol)
    if info is None:
        log.error("Không tìm thấy symbol '%s': %s", symbol, mt5.last_error())
    return info


def get_tick(symbol: str) -> mt5.Tick | None:
    """Lấy giá bid/ask hiện tại."""
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        log.error("Không lấy được tick cho %s: %s", symbol, mt5.last_error())
    return tick
