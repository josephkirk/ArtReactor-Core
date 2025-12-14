from .manager import EventManager, event_manager
from .decorators import event, on


def off(event_name: str, handler):
    event_manager.off(event_name, handler)


__all__ = ["EventManager", "event_manager", "event", "on", "off"]

__all__ = ["EventManager", "event_manager", "event", "on"]
