"""
Schedule Web App - MicroDot-based web interface for Schedule management.
Optimized for MicroPython, works on CPython for development.
"""

try:
    # MicroPython
    from microdot import Microdot, Response, redirect, send_file
    # from microdot.websocket import with_websocket
    import ujson as json
    import uasyncio as asyncio
    MICROPYTHON = True
except ImportError:
    # CPython (development)
    # from microdot import Microdot, Response, redirect
    # try:
    #     from microdot.websocket import with_websocket
    # except ImportError:
    #     with_websocket = None
    import json
    import asyncio
    MICROPYTHON = False

from schedule import Schedule


class ScheduleApp:
    def __init__(self, schedule: Schedule = None):
        self.schedule = schedule or Schedule()
        self.app = Microdot()
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/')
        async def index(request):
            # return Response(body=HTML_TEMPLATE, headers={'Content-Type': 'text/html'})
            return send_file('www/schedule.html')

        @self.app.route('/api/schedule', methods=['GET'])
        async def get_schedule(request):
            """Get current schedule as JSON (1440 minutes for compatibility)."""
            minutes = []
            for m in range(Schedule.MINUTES_PER_DAY):
                minutes.append(self.schedule.is_active_minute(m))

            return {
                'minutes': minutes,
                'hex': self.schedule.to_hex(),
                'active_count': len(self.schedule),
                'intervals_5min': 288  # Indicate 5-min granularity
            }

        @self.app.route('/api/schedule', methods=['POST'])
        async def set_schedule(request):
            """Set schedule from JSON array of 1440 booleans."""
            try:
                data = json.loads(request.body)
                minutes = data.get('minutes', [])

                if len(minutes) != Schedule.MINUTES_PER_DAY:
                    return {'error': f'Expected {Schedule.MINUTES_PER_DAY} minutes'}, 400

                new_schedule = Schedule()
                for i, active in enumerate(minutes):
                    if active:
                        h, m = divmod(i, 60)
                        new_schedule.set_active(h, m, True)

                self.schedule = new_schedule

                return {
                    'success': True,
                    'hex': self.schedule.to_hex(),
                    'active_count': len(self.schedule)
                }
            except Exception as e:
                return {'error': str(e)}, 500

        @self.app.route('/api/schedule/hex', methods=['POST'])
        async def set_schedule_hex(request):
            """Set schedule from hex string."""
            try:
                data = json.loads(request.body)
                hex_str = data.get('hex', '')
                self.schedule = Schedule.from_hex(hex_str)

                minutes = []
                for m in range(Schedule.MINUTES_PER_DAY):
                    minutes.append(self.schedule.is_active_minute(m))

                return {
                    'success': True,
                    'minutes': minutes,
                    'active_count': len(self.schedule)
                }
            except Exception as e:
                return {'error': str(e)}, 400

        @self.app.route('/api/range', methods=['POST'])
        async def set_range(request):
            """Set a range directly (5-min aligned)."""
            try:
                data = json.loads(request.body)
                # Align to 5-minute boundaries
                start_h = data.get('start_h', 0)
                start_m = (data.get('start_m', 0) // 5) * 5
                end_h = data.get('end_h', 0)
                end_m = (data.get('end_m', 0) // 5) * 5

                self.schedule.set_range(start_h, start_m, end_h, end_m,
                                        data.get('active', True))
                return {
                    'success': True,
                    'hex': self.schedule.to_hex(),
                    'aligned': {'start': f'{start_h}:{start_m}', 'end': f'{end_h}:{end_m}'}
                }
            except Exception as e:
                return {'error': str(e)}, 400

        @self.app.route('/api/clear', methods=['POST'])
        async def clear_schedule(request):
            """Clear entire schedule."""
            self.schedule.clear()
            return {'success': True, 'hex': self.schedule.to_hex()}

        @self.app.route('/api/fill', methods=['POST'])
        async def fill_schedule(request):
            """Fill entire schedule."""
            try:
                data = json.loads(request.body) if request.body else {}
                self.schedule.fill(data.get('active', True))
                return {'success': True, 'hex': self.schedule.to_hex()}
            except Exception as e:
                return {'error': str(e)}, 400


