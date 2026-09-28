import enum


class WorkspaceRole(enum.StrEnum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"

    def includes(self, required: WorkspaceRole) -> bool:
        # owner ⊇ editor ⊇ viewer
        order = [WorkspaceRole.VIEWER, WorkspaceRole.EDITOR, WorkspaceRole.OWNER]
        return order.index(self) >= order.index(required)
