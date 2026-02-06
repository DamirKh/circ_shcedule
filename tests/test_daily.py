# tests/test_daily.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import time
from schedule.daily import DailySchedule


def test_full_workflow():
    """Полный тест: работа 9-18 с обедом 12-13 (через set)"""
    s = DailySchedule(default=False)

    # Строим пошагово
    s.set(time(9, 0), True)  # 9:00-... True (пока всё)
    s.set(time(18, 0), False)  # 18:00-9:00 False
    s.set(time(12, 0), False)  # 12:00-18:00 False (обед)
    s.set(time(13, 0), True)  # 13:00-18:00 True

    # Проверки
    assert s.get(time(8, 59)) == False
    assert s.get(time(9, 0)) == True
    assert s.get(time(11, 59)) == True
    assert s.get(time(12, 0)) == False  # Обед
    assert s.get(time(12, 30)) == False
    assert s.get(time(13, 0)) == True  # Работа
    assert s.get(time(17, 59)) == True
    assert s.get(time(18, 0)) == False  # Конец

    # Интервалы
    iv = s.intervals()
    assert len(iv) == 4  # True, False, True, False

    print("✓ Full workflow OK")
    print(f"Intervals: {iv}")


def test_circular_night_shift():
    """Ночная смена 22:00-06:00"""
    s = DailySchedule(default=False)

    s.set(time(22, 0), True)
    s.set(time(6, 0), False)

    assert s.get(time(21, 59)) == False
    assert s.get(time(22, 0)) == True
    assert s.get(time(23, 59)) == True
    assert s.get(time(0, 0)) == True  # Через полночь!
    assert s.get(time(5, 59)) == True
    assert s.get(time(6, 0)) == False

    print("✓ Circular night shift OK")


def test_first_set_fills_all():
    """Первая точка заливает всё кроме последней точки"""
    s = DailySchedule(default=False)

    s.set(time(9, 0), True)
    # True сейчас от 9:00 до 08:58
    assert s.get(time(9, 0)) == True
    assert s.get(time(8, 59)) == False
    assert s.get(time(0, 0)) == True
    assert s.get(time(23, 59)) == True

    s.set(time(18, 0), False)
    # Теперь 9-18 True, остальное False
    assert s.get(time(12, 0)) == True
    assert s.get(time(20, 0)) == False

    print("✓ First set fills all OK")


def test_memory():
    """Проверка памяти"""
    s = DailySchedule()
    assert len(s._data) == 1440
    print(f"✓ Memory: {s.memory_usage()} bytes (base 1440)")


if __name__ == "__main__":
    test_full_workflow()
    test_circular_night_shift()
    test_first_set_fills_all()
    test_memory()
    print("\nAll tests passed!")