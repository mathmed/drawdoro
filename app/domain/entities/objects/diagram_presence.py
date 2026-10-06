import uuid
from dataclasses import dataclass


# Who is in one diagram right now, as the workspace's sidebar shows it. No entries means nobody.
@dataclass(frozen=True)
class DiagramPresence[Entry]:
    diagram_id: str
    project_id: uuid.UUID
    entries: tuple[Entry, ...]
