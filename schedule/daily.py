#schedule.daily
from datetime import time
from typing import List, Tuple
from bisect import bisect_right

class InvalidScheduleError(ValueError):
    """Расписание невалидно (нечётное количество точек)"""
    pass

class CircularDailySchedule:
    """
    Кольцевое расписание на сутки.
    Каждая секунда имеет состояние: True или False.

    Инвариант: расписание валидно только при чётном количестве точек.
    Нечётное количество точек означает незавершённый интервал.
    """

    SECONDS_IN_DAY = 24 * 60 * 60

    def __init__(self, default: bool = False):
        self._points: List[Tuple[int, bool]] = []
        self._default = default

    def _to_seconds(self, t: time) -> int:
        return t.hour * 3600 + t.minute * 60 + t.second

    def _to_time(self, seconds: int) -> time:
        seconds = seconds % self.SECONDS_IN_DAY
        return time(seconds // 3600, (seconds % 3600) // 60, seconds % 60)

    def _normalize(self) -> None:
        if not self._points:
            return

        self._points.sort(key=lambda x: x[0])

        cleaned = []
        prev_state = self._default

        for sec, state in self._points:
            if state == prev_state:
                continue
            if cleaned and cleaned[-1][0] == sec:
                cleaned[-1] = (sec, state)
            else:
                cleaned.append((sec, state))
            prev_state = state

        self._points = cleaned

    def is_valid(self) -> bool:
        """Проверка валидности: чётное количество точек"""
        return len(self._points) % 2 == 0

    def validate(self) -> None:
        """Выбрасывает исключение, если расписание невалидно"""
        if not self.is_valid():
            raise InvalidScheduleError(
                f"Невалидное расписание: {len(self._points)} точек (должно быть чётное)"
            )

    def set(self, t: time, state: bool) -> None:
        sec = self._to_seconds(t)

        if self._points:
            current = self.get(t)
            if current == state:
                idx = bisect_right(self._points, sec, key=lambda x: x[0])
                if idx > 0 and self._points[idx - 1][0] == sec:
                    return

        self._points.append((sec, state))
        self._normalize()

    def get(self, t: time) -> bool:
        """
        Получить состояние на момент t.

        ВАЛИДНОЕ расписание: чётное количество точек, чередование True/False.
        НЕВАЛИДНОЕ расписание: нечётное количество — возвращает default
        или последнее состояние (зависит от реализации).
        """
        if not self._points:
            return self._default

        # При нечётном количестве — расписание незавершено
        # Можно: вернуть default, или всё равно вычислить
        # Выбираем: всё равно вычисляем, но is_valid() == False

        sec = self._to_seconds(t)
        idx = bisect_right(self._points, sec, key=lambda x: x[0]) - 1

        if idx >= 0:
            return self._points[idx][1]
        else:
            return self._points[-1][1]

    def force_validate_on_get(self, t: time) -> bool:
        """get с обязательной проверкой валидности"""
        self.validate()
        return self.get(t)

    def intervals(self) -> List[Tuple[time, time, bool]]:
        """
        Все интервалы постоянного состояния.

        Только для ВАЛИДНОГО расписания (чётное число точек).
        При нечётном — выбрасывает исключение.
        """
        self.validate()

        if not self._points:
            t = time(0, 0, 0)
            return [(t, t, self._default)]

        result = []
        n = len(self._points)

        for i in range(0, n, 2):  # Шаг 2: пары (начало, конец)
            start_sec, state = self._points[i]
            end_sec = self._points[i + 1][0]

            start = self._to_time(start_sec)
            end = self._to_time(end_sec)
            result.append((start, end, state))

        return result

    def __len__(self) -> int:
        return len(self._points)

    def __repr__(self) -> str:
        items = ", ".join(f"{self._to_time(s)}->{int(v)}" for s, v in self._points[:4])
        if len(self._points) > 4:
            items += f"...({len(self._points)} total)"
        valid_mark = "✓" if self.is_valid() else "✗"
        return f"Schedule[{valid_mark}]({items})"