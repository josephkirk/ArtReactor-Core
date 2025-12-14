# Event System

The Event System allows decoupled communication between components.

## Key Features

- Async support
- High performance (100k+ events/second)
- Decorators for easy use
- Fire-and-forget pattern

## Basic Usage

```python
from artreactor.core.events import event, on, fire, off

# Define event
@event
class MyEvent:
    data: str

# Register listener
@on("my.event")
async def handle_event(data: dict):
    print(f"Event received: {data}")

# Fire event
fire("my.event", {"data": "value"})
```

See the [Core Components](core-components.md#eventmanager) documentation for more details.
