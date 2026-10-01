import enum


class CommentStatus(enum.StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    ALL = "all"
