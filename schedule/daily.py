#schedule.daily
from datetime import time
from typing import List, Tuple
from bisect import bisect_right


class CircularDailySchedule:
    """
    Кольцевое расписание на сутки.
    Каждая секунда имеет состояние: True или False.
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
        if not self._points:
            return self._default

        sec = self._to_seconds(t)
        idx = bisect_right(self._points, sec, key=lambda x: x[0]) - 1

        if idx >= 0:
            return self._points[idx][1]
        else:
            return self._points[-1][1]

    def intervals(self) -> List[Tuple[time, time, bool]]:
        """
        Все интервалы постоянного состояния.
        Последний интервал замыкается на первую точку (через полночь).
        """
        if not self._points:
            t = time(0, 0, 0)
            return [(t, t, self._default)]

        result = []
        n = len(self._points)

        for i in range(n):
            start_sec, state = self._points[i]
            # Конец = начало следующей точки (с кольцеванием)
            end_sec = self._points[(i + 1) % n][0]

            start = self._to_time(start_sec)
            end = self._to_time(end_sec)
            result.append((start, end, state))

        return result

    def __len__(self) -> int:
        return len(self._points)

    def __repr__(self) -> str:
        items = ", ".join(f"{self._to_time(s)}->{int(v)}" for s, v in self._points[:3])
        if len(self._points) > 3:
            items += f"...({len(self._points)} total)"
        return f"Schedule({items})"
