import uuid
from dataclasses import dataclass, field


# Someone with a diagram open in the editor, as shown in its presence.
@dataclass(frozen=True)
class Participant:
    name: str
    # None for guests (authentication disabled); they are told apart per connection.
    user_id: str | None = None
    picture_url: str | None = None
    connection_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    @property
    def presence_id(self) -> str:
        return self.user_id or self.connection_id
