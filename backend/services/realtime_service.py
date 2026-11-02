from __future__ import annotations

import threading
from collections import defaultdict
from queue import Queue


class SessionEventBus:
    """Barramento de eventos simples em memória 
    para atualizar a sessão em tempo real."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._subscribers = defaultdict(list)
        return cls._instance

    def subscribe(self, session_id):
        queue = Queue()
        with self._lock:
            self._subscribers[session_id].append(queue)
        return queue

    def unsubscribe(self, session_id, queue):
        with self._lock:
            subscribers = self._subscribers.get(session_id, [])
            if queue in subscribers:
                subscribers.remove(queue)
            if not subscribers:
                self._subscribers.pop(session_id, None)

    def publish(self, session_id, event_name, payload):
        message = {
            "event": event_name,
            "session_id": session_id,
            "data": payload or {},
        }

        with self._lock:
            subscribers = list(self._subscribers.get(session_id, []))

        for subscriber in subscribers:
            try:
                subscriber.put_nowait(message)
            except Exception:
                pass


session_event_bus = SessionEventBus()
