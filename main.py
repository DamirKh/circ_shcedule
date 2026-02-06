# tests/test_daily.py - компактный тест для MicroPython
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import time
from schedule.daily import DailySchedule


def test_basic():
    s = DailySchedule(default=False)

    # Работа 9:00-12:00 и 13:00-18:00 (обед 12:00-13:00)
    s.set_range(time(9, 0), time(12, 0), True)
    s.set_range(time(13, 0), time(18, 0), True)

    # O(1) чтение
    assert s.get(time(8, 59)) == False
    assert s.get(time(9, 0)) == True
    assert s.get(time(12, 0)) == False  # Обед начался
    assert s.get(time(12, 30)) == False
    assert s.get(time(13, 0)) == True  # Обед кончился
    assert s.get(time(18, 0)) == False  # Конец работы

    # Прямой доступ по минуте (быстрее)
    assert s.get_minute(540) == True  # 9*60
    assert s.get_minute(720) == False  # 12*60

    print("OK")
    print(f"Memory: {s.memory_usage()} bytes")


if __name__ == "__main__":
    test_basic()