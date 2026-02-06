from schedule.daily import CircularDailySchedule
from datetime import datetime, time, timedelta

# === Тест ===
from datetime import time

s = CircularDailySchedule(default=False)

# Работаем с 9:00 до 18:00 с перерывом на обед
s.set(time(9, 0, 0), True)
s.set(time(18, 0, 0), False)
s.set(time(12, 0, 0), False)
s.set(time(13, 0, 0), True)

print(f"\nИнтервалы:")
for start, end, state in s.intervals():
    print(f"  {start} - {end}: {state}")

print(s)