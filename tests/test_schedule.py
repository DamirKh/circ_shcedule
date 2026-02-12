"""
Тесты для Schedule. Запускать: pytest tests/test_schedule.py -v
"""

import sys
import pytest

# Добавляем parent dir в path
sys.path.insert(0, '.')

from schedule import Schedule, create_daily, TimeSlot


class TestScheduleBasic:
    """Базовые тесты создания и чтения."""

    def test_create_empty(self):
        s = Schedule()
        assert len(s._data) == 180
        assert s.to_bytes() == bytes(180)

    def test_create_from_bytes(self):
        data = bytes([0xFF] * 180)
        s = Schedule(data)
        assert s.is_active(0, 0) is True
        assert s.is_active(23, 59) is True

    def test_create_from_bytearray(self):
        data = bytearray(180)
        data[0] = 0b00000001  # 00:00 активен
        s = Schedule(data)
        assert s.is_active(0, 0) is True
        assert s.is_active(0, 1) is False

    def test_invalid_data_size(self):
        with pytest.raises(ValueError):
            Schedule(bytes(100))

    def test_time_boundaries(self):
        s = Schedule()
        # Границы суток
        s.set_active(0, 0, True)
        s.set_active(23, 59, True)
        assert s.is_active(0, 0) is True
        assert s.is_active(23, 59) is True


class TestScheduleReadWrite:
    """Тесты записи и чтения."""

    def test_set_and_check_single(self):
        s = Schedule()
        s.set_active(12, 30, True)
        assert s.is_active(12, 30) is True
        assert s.is_active(12, 29) is False
        assert s.is_active(12, 31) is False

    def test_set_false(self):
        s = Schedule()
        s.set_active(10, 0, True)
        s.set_active(10, 0, False)
        assert s.is_active(10, 0) is False

    def test_set_range(self):
        s = Schedule()
        s.set_range(9, 0, 18, 0, True)  # Рабочий день 9-18

        assert s.is_active(8, 59) is False
        assert s.is_active(9, 0) is True
        assert s.is_active(12, 30) is True
        assert s.is_active(17, 59) is True
        assert s.is_active(18, 0) is False

    def test_clear(self):
        s = Schedule(bytes([0xFF] * 180))
        s.clear()
        assert s.to_bytes() == bytes(180)
        assert s.is_active(12, 0) is False

    def test_fill(self):
        s = Schedule()
        s.fill(True)
        assert s.is_active(0, 0) is True
        assert s.is_active(23, 59) is True
        assert len(s) == 1440


class TestScheduleIteration:
    """Тесты итераторов."""

    def test_active_minutes(self):
        s = Schedule()
        s.set_active(0, 5, True)
        s.set_active(0, 10, True)

        minutes = list(s.active_minutes())
        assert minutes == [5, 10]

    def test_active_slots(self):
        s = Schedule()
        s.set_active(1, 2, True)

        slots = list(s.active_slots())
        assert slots == [(1, 2)]

    def test_ranges_single(self):
        s = Schedule()
        s.set_range(10, 0, 12, 30, True)

        ranges = list(s.ranges())
        assert ranges == [((10, 0), (12, 30))]

    def test_ranges_multiple(self):
        s = Schedule()
        s.set_range(9, 0, 10, 0, True)
        s.set_range(14, 0, 15, 0, True)

        ranges = list(s.ranges())
        assert len(ranges) == 2
        assert ranges[0] == ((9, 0), (10, 0))
        assert ranges[1] == ((14, 0), (15, 0))

    def test_ranges_intersection(self):
        """Тест двух взаимно пересекающихся True диапазонов.
        Результат - один объединённый диапазон."""
        s = Schedule()
        # Первый диапазон: 10:00 - 14:00
        s.set_range(10, 0, 14, 0, True)
        # Второй диапазон пересекается с первым: 13:00 - 17:00
        s.set_range(13, 0, 17, 0, True)

        # Должен быть один объединённый диапазон 10:00 - 17:00
        ranges = list(s.ranges())
        assert len(ranges) == 1
        assert ranges[0] == ((10, 0), (17, 0))

        # Проверяем границы
        assert s.is_active(9, 59) is False  # До начала
        assert s.is_active(10, 0) is True  # Начало
        assert s.is_active(13, 30) is True  # В пересечении
        assert s.is_active(16, 59) is True  # Конец
        assert s.is_active(17, 0) is False  # После окончания

    def test_ranges_merge_adjacent(self):
        """Тест слияния смежных диапазонов (границы совпадают)."""
        s = Schedule()
        s.set_range(9, 0, 12, 0, True)  # 9:00 - 12:00
        s.set_range(12, 0, 15, 0, True)  # 12:00 - 15:00 (начало = конец первого)

        ranges = list(s.ranges())
        assert len(ranges) == 1
        assert ranges[0] == ((9, 0), (15, 0))

    def test_range_OFF_over_ON(self):
        """Тест диапазона OFF полностью внутри диапазона ON.
        Результат - два диапазона."""
        s = Schedule()
        # Базовый диапазон ON: 08:00 - 20:00
        s.set_range(8, 0, 20, 0, True)
        # Вырезаем OFF внутри: 12:00 - 13:00 (обеденный перерыв)
        s.set_range(12, 0, 13, 0, False)

        # Должно получиться два диапазона: 08:00-12:00 и 13:00-20:00
        ranges = list(s.ranges())
        assert len(ranges) == 2
        assert ranges[0] == ((8, 0), (12, 0))
        assert ranges[1] == ((13, 0), (20, 0))

        # Проверяем границы
        assert s.is_active(7, 59) is False  # До начала
        assert s.is_active(8, 0) is True  # Начало первого
        assert s.is_active(11, 59) is True  # Конец первого
        assert s.is_active(12, 0) is False  # Начало перерыва
        assert s.is_active(12, 30) is False  # Середина перерыва
        assert s.is_active(12, 59) is False  # Конец перерыва
        assert s.is_active(13, 0) is True  # Начало второго
        assert s.is_active(19, 59) is True  # Конец второго
        assert s.is_active(20, 0) is False  # После окончания

    def test_range_OFF_partially_over_ON(self):
        """Диапазон OFF частично накладывается на диапазон ON.
        Результат - диапазон ON меньше первоначального."""
        s = Schedule()
        # Базовый диапазон ON: 10:00 - 16:00
        s.set_range(10, 0, 16, 0, True)
        # Частичное наложение OFF: 14:00 - 18:00 (перекрывает конец ON)
        s.set_range(14, 0, 18, 0, False)

        # Должен остаться один укороченный диапазон: 10:00 - 14:00
        ranges = list(s.ranges())
        assert len(ranges) == 1
        assert ranges[0] == ((10, 0), (14, 0))

        # Проверяем границы
        assert s.is_active(9, 59) is False  # До начала
        assert s.is_active(10, 0) is True  # Начало
        assert s.is_active(13, 59) is True  # До границы OFF
        assert s.is_active(14, 0) is False  # Начало OFF-диапазона
        assert s.is_active(16, 0) is False  # Было окончанием ON, теперь OFF
        assert s.is_active(17, 59) is False  # Внутри OFF
        assert s.is_active(18, 0) is False  # После OFF


class TestScheduleSerialization:
    """Тесты сериализации."""

    def test_roundtrip_bytes(self):
        s = Schedule()
        s.set_range(8, 0, 20, 0, True)

        data = s.to_bytes()
        s2 = Schedule.from_bytes(data)

        assert s == s2

    def test_roundtrip_hex(self):
        s = Schedule()
        s.set_active(12, 0, True)

        hex_str = s.to_hex()
        s2 = Schedule.from_hex(hex_str)

        assert s == s2
        assert len(hex_str) == 360  # 180 * 2

    def test_hex_format(self):
        s = Schedule()
        hex_str = s.to_hex()
        assert all(c in '0123456789abcdef' for c in hex_str)


class TestScheduleHelpers:
    """Тесты вспомогательных функций."""

    def test_create_daily(self):
        s = create_daily(9, 18)
        assert s.is_active(9, 0) is True
        assert s.is_active(17, 59) is True
        assert s.is_active(18, 0) is False

    def test_len_empty(self):
        s = Schedule()
        assert len(s) == 0

    def test_len_full(self):
        s = Schedule(bytes([0xFF] * 180))
        # 180 * 8 = 1440, но последние 4 бита не используются (1440 % 8 = 0)
        assert len(s) == 1440

    def test_copy(self):
        s1 = Schedule()
        s1.set_active(10, 0, True)
        s2 = s1.copy()

        assert s1 == s2
        s2.set_active(11, 0, True)
        assert s1 != s2  # Независимые копии


# === Интеграционные тесты ===

def test_real_world_schedule():
    """Тест реального сценария: рабочие часы с перерывом."""
    work = Schedule()
    # Утро: 9:00 - 13:00
    work.set_range(9, 0, 13, 0, True)
    # Обед: 13:00 - 14:00 - перерыв (неактивно)
    # Вечер: 14:00 - 18:00
    work.set_range(14, 0, 18, 0, True)

    assert len(work) == 8 * 60  # 8 часов

    ranges = list(work.ranges())
    assert len(ranges) == 2
    assert ranges[0] == ((9, 0), (13, 0))
    assert ranges[1] == ((14, 0), (18, 0))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
