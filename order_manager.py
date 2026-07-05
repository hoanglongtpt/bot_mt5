"""
order_manager.py — Tính SL/TP theo USD, đặt lệnh, monitor vị thế

Công thức tính SL/TP pips:
    pip_value = tick_value / tick_size * pip_size * lot
    sl_pips   = SL_USD / pip_value
    tp_pips   = TP_USD / pip_value

    sl_price  = ask - sl_pips * pip_size   (BUY)
    tp_price  = ask + tp_pips * pip_size   (BUY)
"""

from typing import Optional
import MetaTrader5 as mt5

from logger_setup import get_logger
import config
from connector import get_symbol_info, get_tick, ensure_connected

log = get_logger("order_manager")


# ─────────────────────────────────────────
# Tính SL / TP
# ─────────────────────────────────────────

def _pip_size(info: mt5.SymbolInfo) -> float:
    """
    Trả về kích thước 1 pip.
    Broker 5 chữ số (digits=5): pip = 10 * point
    Broker 4 chữ số (digits=4): pip = point
    XAU/USD (digits=2): pip = point
    """
    if info.digits in (5, 3):
        return info.point * 10
    return info.point


def calc_sl_tp_prices(
    symbol: str,
    order_type: str,   # "BUY" | "SELL"
    entry_price: float,
    sl_usd: float = config.SL_USD,
    tp_usd: float = config.TP_USD,
    lot: float = config.LOT_SIZE,
) -> Optional[tuple[float, float]]:
    """
    Tính giá SL và TP để đạt đúng sl_usd / tp_usd với lot đã cho.
    Trả về (sl_price, tp_price) hoặc None nếu lỗi.
    """
    info = get_symbol_info(symbol)
    if info is None:
        return None

    pip = _pip_size(info)

    # pip_value = giá trị 1 pip cho số lot đang dùng (USD)
    # tick_value: giá trị 1 tick (minimum move) cho 1 lot
    # tick_size: kích thước 1 tick
    pip_value = (info.trade_tick_value / info.trade_tick_size) * pip * lot

    if pip_value <= 0:
        log.error("pip_value không hợp lệ (%.8f) cho %s", pip_value, symbol)
        return None

    sl_pips = sl_usd / pip_value
    tp_pips = tp_usd / pip_value

    log.debug("%s | pip=%.5f | pip_value=$%.4f | SL=%.1f pips | TP=%.1f pips",
              symbol, pip, pip_value, sl_pips, tp_pips)

    if order_type == "BUY":
        sl_price = round(entry_price - sl_pips * pip, info.digits)
        tp_price = round(entry_price + tp_pips * pip, info.digits)
    else:  # SELL
        sl_price = round(entry_price + sl_pips * pip, info.digits)
        tp_price = round(entry_price - tp_pips * pip, info.digits)

    return sl_price, tp_price


# ─────────────────────────────────────────
# Đặt lệnh
# ─────────────────────────────────────────

def place_order(
    symbol: str,
    order_type: str,   # "BUY" | "SELL"
    lot: float = config.LOT_SIZE,
    sl_usd: float = config.SL_USD,
    tp_usd: float = config.TP_USD,
) -> Optional[mt5.OrderSendResult]:
    """
    Đặt lệnh market BUY/SELL với SL/TP tính theo USD.
    Trả về kết quả mt5.order_send() hoặc None nếu thất bại.
    """
    if not ensure_connected():
        return None

    tick = get_tick(symbol)
    if tick is None:
        return None

    entry = tick.ask if order_type == "BUY" else tick.bid
    prices = calc_sl_tp_prices(symbol, order_type, entry, sl_usd, tp_usd, lot)
    if prices is None:
        return None

    sl_price, tp_price = prices
    mt5_type = mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL

    request = {
        "action":       mt5.TRADE_ACTION_DEAL,
        "symbol":       symbol,
        "volume":       lot,
        "type":         mt5_type,
        "price":        entry,
        "sl":           sl_price,
        "tp":           tp_price,
        "deviation":    10,        # slippage tối đa 10 điểm
        "magic":        config.MAGIC,
        "comment":      "bot_mt5",
        "type_time":    mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        log.error("Đặt lệnh %s %s thất bại | retcode=%s | comment=%s",
                  order_type, symbol,
                  result.retcode if result else "None",
                  result.comment if result else "")
        return None

    log.info("Lệnh %s %s | ticket=#%d | lot=%.2f | entry=%.5f | SL=%.5f | TP=%.5f",
             order_type, symbol, result.order, lot, entry, sl_price, tp_price)
    return result


# ─────────────────────────────────────────
# Quản lý vị thế
# ─────────────────────────────────────────

def get_open_positions(symbol: str = None) -> list:
    """Lấy danh sách vị thế đang mở do bot này (theo MAGIC)."""
    if not ensure_connected():
        return []
    positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
    if positions is None:
        return []
    return [p for p in positions if p.magic == config.MAGIC]


def log_open_positions() -> None:
    """In trạng thái tất cả vị thế bot đang giữ."""
    positions = get_open_positions()
    if not positions:
        log.info("Không có vị thế nào đang mở")
        return
    for p in positions:
        direction = "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL"
        log.info("Vị thế #%d | %s %s | lot=%.2f | profit=%.2f$ | SL=%.5f | TP=%.5f",
                 p.ticket, direction, p.symbol, p.volume, p.profit, p.sl, p.tp)
