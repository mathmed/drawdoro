import uuid
from dataclasses import dataclass


# Where a diagram sits: which workspace's members may see who is in it, and under which project.
@dataclass(frozen=True)
class DiagramLocation:
    workspace_id: uuid.UUID
    project_id: uuid.UUID
