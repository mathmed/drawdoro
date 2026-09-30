import enum


class RevisionOrigin(enum.StrEnum):
    HUMAN = "human"
    AGENT = "agent"
