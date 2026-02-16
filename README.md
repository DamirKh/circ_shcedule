# MicroPython Schedule Manager

Compact schedule storage and web-based configuration tool for MicroPython with CPython compatibility. Optimized for ESP32/ESP8266 microcontrollers with limited resources.

## Features

- **Memory Efficient**: 180 bytes per schedule (1440 minutes as bit mask)
- **5-Minute Web UI**: Interactive grid for easy schedule configuration
- **Dual Environment**: Runs on both MicroPython (hardware) and CPython (development)
- **Minimal Dependencies**: Only Microdot and asyncio required
- **REST API**: JSON/Hex import-export for integration
- **Mobile Friendly**: Touch-optimized responsive interface

## Project Structure

<pre>
schedule/
├── schedule.py          # Core Schedule class (CPython/MicroPython)
├── start_web_app.py     # MicroDot web application
├── www/
│   └── schedule.html    # HTML for web interface
├── tests/
│   └── test_schedule.py # pytest test suite
└── README.md            # This file
</pre>


## Quick Start

### CPython (Development)

```bash
# Install dependencies
pip install microdot pytest

# Run tests
pytest tests/test_schedule.py -v

# Start web server for development
python start_web_app.py
# Open http://localhost:5000
```
### Core API (schedule.py)
Schedule Class
```
from schedule import Schedule

# Create empty schedule
s = Schedule()

# Set range (9:00 to 18:00)
s.set_range(9, 0, 18, 0, True)

# Check specific time
is_working = s.is_active(14, 30)  # True

# Serialize
hex_string = s.to_hex()           # 360 char hex
raw_bytes = s.to_bytes()          # 180 bytes

# Deserialize
s2 = Schedule.from_hex(hex_string)

```
### Key Methods
| Method                           | Description          | Complexity |
| -------------------------------- | -------------------- | ---------- |
| `is_active(h, m)`                | Check state at time  | O(1)       |
| `set_active(h, m, val)`          | Set single minute    | O(1)       |
| `set_range(sh, sm, eh, em, val)` | Set time range       | O(n)       |
| `ranges()`                       | Get active intervals | O(1440)    |
| `to_hex()` / `from_hex()`        | Serialize            | O(180)     |


# Web Interface
### Features
5-Minute Grid: 24 hours × 12 intervals (00-55 min)
Drag to Paint: Click and drag to toggle multiple cells
Hour Inversion: Click hour label (00-23) to toggle entire hour
Quick Presets: Work day, night mode, daylight, all on/off
Range Editor: Set specific time ranges on/off
Import/Export: Hex string or compact format (09:00-18:00,22:00-06:00)

# Endpoints
| Endpoint            | Method | Description                           |
| ------------------- | ------ | ------------------------------------- |
| `/`                 | GET    | Web interface                         |
| `/api/schedule`     | GET    | Get schedule as 1440 bool array + hex |
| `/api/schedule`     | POST   | Set schedule from bool array          |
| `/api/schedule/hex` | POST   | Import from hex string                |
| `/api/range`        | POST   | Set range (auto 5-min aligned)        |
| `/api/clear`        | POST   | Clear all                             |
| `/api/fill`         | POST   | Fill all on/off                       |

# Memory Usage
| Component        | MicroPython       | CPython    |
| ---------------- | ----------------- | ---------- |
| Schedule object  | ~200 bytes        | ~280 bytes |
| Web app (loaded) | ~15 KB            | ~25 KB     |
| HTML template    | ~35 KB (embedded) | ~35 KB     |

# Testing
<pre>
# Run all tests
pytest tests/test_schedule.py -v

# With coverage
pytest tests/test_schedule.py --cov=schedule --cov-report=html

# Benchmarks
pytest tests/test_schedule.py --benchmark-only
</pre>
### Test Coverage
 - Basic read/write operations
 - Range manipulations (ON/OFF overlap scenarios)
 - Serialization round-trips
 - Edge cases (midnight boundaries, empty ranges)
 - Performance benchmarks

# License
MIT License - Free for personal and commercial use.

# Contributing
 - Fork the repository
 - Create feature branch (git checkout -b feature/amazing)
 - Commit changes (git commit -m 'Add amazing feature')
 - Push to branch (git push origin feature/amazing)
 - Open Pull Request
