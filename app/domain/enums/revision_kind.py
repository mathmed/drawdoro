import enum


class RevisionKind(enum.StrEnum):
    # A save by a person or an agent.
    EDIT = "edit"
    # A save that brought back an earlier revision.
    RESTORE = "restore"
    # The state found before the first recorded change, e.g. diagrams older than the history.
    BASELINE = "baseline"
