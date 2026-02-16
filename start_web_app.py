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
from mdot_schedule import ScheduleApp

def create_app(schedule: Schedule = None) -> ScheduleApp:
    """Create app instance."""
    return ScheduleApp(schedule)


def run_server(schedule: Schedule = None, host='0.0.0.0', port=80):
    """Quick start server."""
    app = ScheduleApp(schedule)
    app.run(host=host, port=port)


# Example usage / Development server
if __name__ == '__main__':
    # Create sample schedule for testing
    test_schedule = Schedule()
    test_schedule.set_range(9, 0, 18, 0, True)  # Work hours

    print("Starting development server...")
    print("Open http://localhost:5000/schedule/ in your browser")

    web_schedule_cntrl = ScheduleApp(test_schedule)

    main_app = Microdot()
    main_app.mount(web_schedule_cntrl.app, url_prefix='/schedule')

    main_app.run(host='localhost', port=5000, debug=True)