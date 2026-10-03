from typing import Protocol


# One editor's live connection to a diagram. A protocol rather than a base class, so the web
# framework's WebSocket fits as it is and the rooms never depend on the framework.
class RealtimeConnection(Protocol):
    async def accept(self) -> None: ...

    async def send_text(self, data: str) -> None: ...
