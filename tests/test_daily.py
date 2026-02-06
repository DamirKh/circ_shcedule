# tests/test_daily.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import time
import pytest
from schedule.daily import CircularDailySchedule, InvalidScheduleError


class TestValidation:
    """Тесты валидации (чётное/нечётное количество точек)"""

    def test_empty_is_valid(self):
        """Пустое расписание — валидно (0 точек, чётное)"""
        s = CircularDailySchedule(default=False)
        assert s.is_valid() is True

    def test_one_point_invalid(self):
        """Одна точка — невалидно"""
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        assert len(s) == 1
        assert s.is_valid() is False

    def test_two_points_valid(self):
        """Две точки — валидно"""
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(18, 0, 0), False)
        assert len(s) == 2
        assert s.is_valid() is True

    def test_three_points_invalid(self):
        """Три точки — невалидно"""
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(12, 0, 0), False)
        s.set(time(15, 0, 0), True)
        assert len(s) == 3
        assert s.is_valid() is False

    def test_four_points_valid(self):
        """Четыре точки — валидно"""
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(12, 0, 0), False)
        s.set(time(15, 0, 0), True)
        s.set(time(18, 0, 0), False)
        assert len(s) == 4
        assert s.is_valid() is True


class TestValidationExceptions:
    """Исключения при работе с невалидным расписанием"""

    def test_validate_raises_on_invalid(self):
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)  # Одна точка

        with pytest.raises(InvalidScheduleError):
            s.validate()

    def test_intervals_raises_on_invalid(self):
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)

        with pytest.raises(InvalidScheduleError):
            s.intervals()

    def test_force_validate_on_get_raises(self):
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)

        with pytest.raises(InvalidScheduleError):
            s.force_validate_on_get(time(10, 0, 0))


class TestIntervalsValidOnly:
    """Интервалы только для валидного расписания"""

    def test_intervals_two_points(self):
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(18, 0, 0), False)

        # Валидно — интервалы работают
        intervals = s.intervals()
        assert len(intervals) == 1
        assert intervals[0] == (time(9, 0, 0), time(18, 0, 0), True)

    def test_intervals_four_points(self):
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(12, 0, 0), False)
        s.set(time(15, 0, 0), True)
        s.set(time(18, 0, 0), False)

        intervals = s.intervals()
        assert len(intervals) == 2
        assert intervals[0] == (time(9, 0, 0), time(12, 0, 0), True)
        assert intervals[1] == (time(15, 0, 0), time(18, 0, 0), True)

    def test_intervals_empty(self):
        s = CircularDailySchedule(default=False)
        intervals = s.intervals()
        assert len(intervals) == 1
        assert intervals[0] == (time(0, 0, 0), time(0, 0, 0), False)


class TestGetWithoutValidation:
    """get() работает даже с невалидным, но is_valid проверяет"""

    def test_get_works_on_invalid(self):
        """get() не выбрасывает исключение, но is_valid == False"""
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)  # Невалидно

        # get() работает (возвращает что-то)
        result = s.get(time(10, 0, 0))
        assert result is True

        # но расписание помечено невалидным
        assert s.is_valid() is False


class TestNormalizationAffectsValidity:
    """Нормализация и валидность"""

    def test_same_second_replace_leaves_invalid(self):
        """Замена в той же секунде: остаётся 1 точка — невалидно"""
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(9, 0, 0), False)

        assert len(s) == 1
        assert s.is_valid() is False

    def test_three_points_invalid_four_valid(self):
        """3 точки — невалидно, 4 точки — валидно"""
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(12, 0, 0), False)
        s.set(time(15, 0, 0), True)

        assert len(s) == 3
        assert s.is_valid() is False

        s.set(time(18, 0, 0), False)
        assert len(s) == 4
        assert s.is_valid() is True

    def test_consecutive_same_state_removed(self):
        """Удаление подряд одинаковых состояний"""
        s = CircularDailySchedule(default=False)
        s.set(time(9, 0, 0), True)
        s.set(time(10, 0, 0), True)  # Дубликат, удалится
        s.set(time(12, 0, 0), False)  # Должно остаться 2 точки

        assert len(s) == 2
        assert s.is_valid() is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])