"""
risk_manager.py — Kiểm soát điều kiện trước khi vào lệnh

Hiện tại quản lý:
  - Số lệnh đang mở không vượt quá MAX_OPEN_ORDERS
"""

from logger_setup import get_logger
import config
from order_manager import get_open_positions

log = get_logger("risk_manager")


def can_trade(symbol: str) -> bool:
    """
    Trả về True nếu được phép vào thêm lệnh.
    Trả về False và log lý do nếu bị chặn.
    """
    open_positions = get_open_positions()
    count = len(open_positions)

    if count >= config.MAX_OPEN_ORDERS:
        log.debug("Đang có %d/%d lệnh mở — chờ lệnh cũ đóng trước",
                  count, config.MAX_OPEN_ORDERS)
        return False

    # Không được mở 2 lệnh cùng chiều trên cùng symbol
    symbol_positions = [p for p in open_positions if p.symbol == symbol]
    if symbol_positions:
        log.debug("Đã có %d lệnh trên %s — bỏ qua", len(symbol_positions), symbol)
        return False

    return True
