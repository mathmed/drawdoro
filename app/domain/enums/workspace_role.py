import enum


class WorkspaceRole(enum.StrEnum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"
