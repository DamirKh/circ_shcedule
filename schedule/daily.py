# schedule/daily.py
from datetime import time
from typing import List, Tuple

D={
    False: 0,
    True: 255
}

class DailySchedule:
    """
    Кольцевое расписание на сутки, гранулярность 1 минута.
    Оптимизировано для MicroPython: 1440 байт, O(1) чтение.
    """

    MINUTES_IN_DAY = 1440

    def __init__(self, default: bool = False):
        self._default = D[default]
        self._data = bytearray(self.MINUTES_IN_DAY)
        for i in range(1, self.MINUTES_IN_DAY):
            self._data[i] = self._default
        self._points = None

    def _to_minutes(self, t: time) -> int:
        return t.hour * 60 + t.minute

    def _invalidate(self) -> None:
        self._points = None

    def set(self, t: time, state: bool) -> None:
        minute = self._to_minutes(t)
        new_val = D[state]

        if self._data[minute] == new_val:
            return
        c=0
        for n in range(self.MINUTES_IN_DAY):
            i = (minute + n) % self.MINUTES_IN_DAY
            if self._data[i] == new_val:
                break
            c+=1
            self._data[i] = new_val

        if c==self.MINUTES_IN_DAY:
            # Обошли полный круг (не первая итерация и вернулись на старт)
            prev = (minute - 1) % self.MINUTES_IN_DAY
            self._data[prev] = D[not state]

        self._invalidate()

    def set_range(self, start: time, end: time, state: bool) -> None:
        """Установить состояние на интервал [start, end)."""
        start_m = self._to_minutes(start)
        end_m = self._to_minutes(end)
        val = D[state]
        data = self._data

        if start_m < end_m:
            for i in range(start_m, end_m):
                data[i] = val
        elif start_m > end_m:
            for i in range(start_m, self.MINUTES_IN_DAY):
                data[i] = val
            for i in range(0, end_m):
                data[i] = val

        self._invalidate()

    def fill(self, state: bool) -> None:
        """Заполнить всё расписание одним состоянием."""
        val = D[state]
        for i in range(self.MINUTES_IN_DAY):
            self._data[i] = val
        self._invalidate()

    def get(self, t: time) -> bool:
        """O(1) чтение состояния на момент t."""
        minute = self._to_minutes(t)
        return bool(self._data[minute])

    def get_minute(self, minute: int) -> bool:
        """Прямой доступ по номеру минуты 0-1439."""
        return bool(self._data[minute])

    def _build_points(self) -> None:
        """Построить список точек изменения (лениво)."""
        self._points = []
        prev = self._default

        for minute in range(self.MINUTES_IN_DAY):
            curr = self._data[minute]
            if curr != prev:
                self._points.append((minute, bool(curr)))
                prev = curr

    def intervals(self) -> List[Tuple[time, time, bool]]:
        """
        Вернуть интервалы постоянного состояния.
        Кольцевой последний интервал замыкается на первый.
        """
        if self._points is None:
            self._build_points()

        if not self._points:
            t = time(0, 0)
            return [(t, t, bool(self._default))]

        result = []
        n = len(self._points)

        for i in range(n):
            start_m, state = self._points[i]
            end_m = self._points[(i + 1) % n][0]

            start = time(start_m // 60, start_m % 60)
            end = time(end_m // 60, end_m % 60)
            result.append((start, end, state))

        return result

    def memory_usage(self) -> int:
        """Примерное использование памяти в байтах."""
        base = len(self._data)
        points = len(self._points) * 8 if self._points else 0
        return base + points

    def __repr__(self) -> str:
        return f"Schedule({self.MINUTES_IN_DAY}m, ~{self.memory_usage()}b)"
