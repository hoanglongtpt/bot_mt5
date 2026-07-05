"""
main.py — Vòng lặp chính của bot MT5

Chu trình mỗi tick:
  1. Đợi đến khi nến M5 mới mở (nến cũ vừa đóng)
  2. Lấy 100 nến gần nhất
  3. Tính indicators
  4. Phát hiện tín hiệu BUY/SELL
  5. Kiểm tra risk (max open orders)
  6. Đặt lệnh nếu đủ điều kiện
  7. Log trạng thái
  8. Lặp lại

Bot chạy VÔ HẠN — chỉ dừng khi Ctrl+C hoặc lỗi nghiêm trọng không thể recover.
"""

import time
import signal
import sys
from datetime import datetime

import MetaTrader5 as mt5

import config
from logger_setup import get_logger
from connector import connect, disconnect, get_candles, ensure_connected
from analyzer import add_indicators
from strategy import detect_signal
from order_manager import place_order, log_open_positions
from risk_manager import can_trade

log = get_logger("main")

_running = True


def _handle_signal(signum, frame):
    """Xử lý Ctrl+C — tắt bot sạch sẽ."""
    global _running
    log.info("Nhận tín hiệu dừng (Ctrl+C) — đang thoát...")
    _running = False


def _wait_for_new_candle(symbol: str, timeframe: int) -> bool:
    """
    Đợi cho đến khi nến M5 mới bắt đầu (nến cũ vừa đóng).
    Trả về True khi nến mới xuất hiện, False nếu lỗi.
    """
    last_candle_time = None

    while _running:
        if not ensure_connected():
            time.sleep(10)
            continue

        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
        if rates is None or len(rates) == 0:
            time.sleep(5)
            continue

        current_candle_time = rates[0]["time"]

        if last_candle_time is None:
            last_candle_time = current_candle_time
            time.sleep(config.LOOP_SLEEP_SECONDS)
            continue

        if current_candle_time != last_candle_time:
            last_candle_time = current_candle_time
            log.debug("Nến mới mở lúc %s",
                      datetime.utcfromtimestamp(current_candle_time).strftime("%Y-%m-%d %H:%M"))
            return True

        time.sleep(config.LOOP_SLEEP_SECONDS)

    return False


def run() -> None:
    log.info("=" * 60)
    log.info("Bot MT5 khởi động | Symbol: %s | TF: M5 | Lot: %.2f",
             config.SYMBOL, config.LOT_SIZE)
    log.info("SL: $%.1f | TP: $%.1f | Max lệnh: %d",
             config.SL_USD, config.TP_USD, config.MAX_OPEN_ORDERS)
    log.info("=" * 60)

    # Kết nối MT5
    if not connect():
        log.critical("Không kết nối được MT5 — bot dừng")
        sys.exit(1)

    iteration = 0

    try:
        while _running:
            # Đợi nến M5 mới
            if not _wait_for_new_candle(config.SYMBOL, config.TIMEFRAME):
                break

            iteration += 1
            log.info("── Chu kỳ #%d ──────────────────────────────", iteration)

            # 1. Lấy nến
            df = get_candles(config.SYMBOL, config.TIMEFRAME, config.CANDLES)
            if df is None or len(df) < 30:
                log.warning("Không đủ dữ liệu nến — bỏ qua chu kỳ này")
                continue

            # 2. Tính indicators
            df = add_indicators(df)

            # 3. Phát hiện tín hiệu
            signal = detect_signal(df)

            # 4. Kiểm tra risk
            if signal and can_trade(config.SYMBOL):
                # 5. Đặt lệnh
                result = place_order(
                    symbol=config.SYMBOL,
                    order_type=signal,
                )
                if result:
                    log.info("Lệnh đặt thành công — ticket #%d", result.order)
                else:
                    log.warning("Đặt lệnh thất bại — xem log chi tiết")

            # 6. Log trạng thái vị thế hiện tại
            log_open_positions()

    except KeyboardInterrupt:
        log.info("Bot dừng do người dùng (KeyboardInterrupt)")
    except Exception as exc:
        log.exception("Lỗi không xử lý được: %s", exc)
    finally:
        disconnect()
        log.info("Bot đã thoát sau %d chu kỳ", iteration)


if __name__ == "__main__":
    signal.signal(signal.SIGINT,  _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)
    run()
