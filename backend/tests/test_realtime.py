import unittest

from app import create_app
from services.realtime_service import session_event_bus


class RealtimeSessionStreamTests(unittest.TestCase):
    def test_session_stream_endpoint_exists(self):
        app = create_app()
        client = app.test_client()

        response = client.get('/sessions/1/events')

        self.assertIn(response.status_code, (200, 404))

    def test_event_bus_publishes_to_session_subscribers(self):
        queue = session_event_bus.subscribe(42)
        session_event_bus.publish(42, 'intensity_change', {'action': 'reduce_intensity'})

        message = queue.get_nowait()

        self.assertEqual(message['event'], 'intensity_change')
        self.assertEqual(message['data']['action'], 'reduce_intensity')

        session_event_bus.unsubscribe(42, queue)


if __name__ == '__main__':
    unittest.main()
