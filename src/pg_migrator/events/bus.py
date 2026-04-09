from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional


class MigrationEventType(Enum):
    """Types of migration events."""
    LOG = auto()
    PROGRESS = auto()
    STEP_START = auto()
    STEP_COMPLETE = auto()
    STEP_SKIP = auto()
    STEP_FAIL = auto()
    STATS_UPDATE = auto()
    COMPLETED = auto()
    ERROR = auto()


@dataclass
class MigrationEvent:
    """Event data structure."""
    type: MigrationEventType
    message: str = ""
    current: int = 0
    total: int = 0
    payload: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Simple synchronous event bus for decoupling engine from UI."""

    def __init__(self):
        self._listeners: Dict[MigrationEventType, List[Callable[[MigrationEvent], None]]] = {
            t: [] for t in MigrationEventType
        }
        self._all_listeners: List[Callable[[MigrationEvent], None]] = []

    def subscribe(self, event_type: MigrationEventType, callback: Callable[[MigrationEvent], None]):
        """Subscribe to a specific event type."""
        self._listeners[event_type].append(callback)

    def subscribe_all(self, callback: Callable[[MigrationEvent], None]):
        """Subscribe to all events."""
        self._all_listeners.append(callback)

    def publish(self, event: MigrationEvent):
        """Publish an event to all subscribers."""
        # Type-specific listeners
        for callback in self._listeners.get(event.type, []):
            callback(event)
        
        # Global listeners
        for callback in self._all_listeners:
            callback(event)


# Global event bus instance
_bus = EventBus()

def get_event_bus() -> EventBus:
    """Get the global event bus."""
    return _bus
