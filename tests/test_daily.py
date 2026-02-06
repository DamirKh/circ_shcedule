# tests/test_daily.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import time
import pytest
from schedule.daily import CircularDailySchedule


class TestInitialization:
    """Тесты конструктора"""

    def test_default_false(self):
        s = CircularDailySchedule(default=False)
        assert s.get(time(0, 0, 0)) is False
        assert len(s) == 0

    def test_default_true(self):
        s = CircularDailySchedule(default=True)
        assert s.get(time(0, 0, 0)) is True
        assert len(s) == 0


class TestBasicSetGet:
    """Базовые операции set/get"""

    def test_single_point_sets_all_day(self):
        """Одна точка = состояние на весь день (чистое кольцо)"""
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)

        # Весь день True, т.к. одна точка замыкается сама на себя
        assert s.get(time(8, 59, 59)) is True  # До точки = после точки (кольцо)
        assert s.get(time(9, 0, 0)) is True
        assert s.get(time(12, 0, 0)) is True
        assert s.get(time(23, 59, 59)) is True

    def test_two_points_create_interval(self):
        """Две точки = два интервала"""
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(18, 0, 0), False)

        assert s.get(time(6, 0, 0)) is False  # До 09:00 = после 18:00 (кольцо)
        assert s.get(time(9, 0, 0)) is True
        assert s.get(time(12, 0, 0)) is True
        assert s.get(time(18, 0, 0)) is False
        assert s.get(time(22, 0, 0)) is False

    def test_set_back_to_false(self):
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(18, 0, 0), False)

        assert s.get(time(12, 0, 0)) is True
        assert s.get(time(20, 0, 0)) is False


class TestCircularBehavior:
    """Чистое кольцевое поведение"""

    def test_before_first_point_uses_last_point(self):
        """До первой точки = состояние последней точки (кольцо)"""
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(18, 0, 0), False)

        # До 09:00 = после 18:00 = False
        assert s.get(time(0, 0, 0)) is False
        assert s.get(time(6, 0, 0)) is False
        assert s.get(time(8, 59, 59)) is False

    def test_single_point_full_circle(self):
        """Одна точка = полный круг"""
        s = CircularDailySchedule(default=False)
        s.set(time(22, 0, 0), True)

        assert s.get(time(23, 59, 59)) is True
        assert s.get(time(0, 0, 0)) is True  # Кольцо с 22:00
        assert s.get(time(21, 59, 59)) is True  # До точки = после точки
        assert s.get(time(22, 0, 0)) is True

    def test_default_only_when_empty(self):
        """Default только в пустом расписании"""
        s = CircularDailySchedule(default=False)
        assert s.get(time(0, 0, 0)) is False

        s.set(time(12, 0, 0), True)
        # Теперь весь день True, default не используется
        assert s.get(time(0, 0, 0)) is True


class TestNormalization:
    """Удаление дубликатов"""

    def test_removes_consecutive_same_state(self):
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(10, 0, 0), True)

        assert len(s) == 1

    def test_same_second_replaces(self):
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(9, 0, 0), False)

        assert len(s) == 1
        assert s.get(time(9, 0, 0)) is False


class TestIntervals:
    """Метод intervals()"""

    def test_empty_schedule(self):
        s = CircularDailySchedule(default=False)
        intervals = s.intervals()

        assert len(intervals) == 1
        assert intervals[0] == (time(0, 0, 0), time(0, 0, 0), False)

    def test_single_point_zero_interval(self):
        """Одна точка = интервал от неё до неё (весь день)"""
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)

        intervals = s.intervals()
        assert len(intervals) == 1
        assert intervals[0] == (time(9, 0, 0), time(9, 0, 0), True)

    def test_two_points_circular(self):
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(18, 0, 0), False)

        intervals = s.intervals()

        assert len(intervals) == 2
        assert intervals[0] == (time(9, 0, 0), time(18, 0, 0), True)
        assert intervals[1] == (time(18, 0, 0), time(9, 0, 0), False)


class TestEdgeCases:
    """Краевые случаи"""

    def test_exact_boundaries(self):
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(18, 0, 0), False)

        # Границы включительно слева
        assert s.get(time(9, 0, 0)) is True
        assert s.get(time(17, 59, 59)) is True
        assert s.get(time(18, 0, 0)) is False

    def test_last_second_of_day(self):
        s = CircularDailySchedule(default=False)
        s.set(time(23, 59, 59), True)

        assert s.get(time(23, 59, 59)) is True
        assert s.get(time(0, 0, 0)) is True  # Кольцо

    def test_first_second_of_day(self):
        s = CircularDailySchedule(default=False)
        s.set(time(0, 0, 0), True)

        assert s.get(time(0, 0, 0)) is True
        assert s.get(time(23, 59, 59)) is True  # Кольцо на себя


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
