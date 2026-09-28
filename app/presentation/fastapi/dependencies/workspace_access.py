import uuid

from fastapi import Depends, Request

from app.domain.entities.models.user import User
from app.domain.entities.models.workspace_member import WorkspaceMember
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.usecases.auth.authorize_workspace_access import (
    AuthorizeWorkspaceAccess,
    AuthorizeWorkspaceAccessParams,
)
from app.presentation.factories.auth_factories import authorize_workspace_access_factory
from app.presentation.fastapi.dependencies.current_user import get_current_user

READ_METHODS = {"GET", "HEAD", "OPTIONS"}
RESOURCE_PARAMS = ("workspace_id", "project_id", "folder_id", "diagram_id")


def _path_ids(request: Request) -> dict[str, uuid.UUID]:
    ids: dict[str, uuid.UUID] = {}
    for key in RESOURCE_PARAMS:
        raw = request.path_params.get(key)
        try:
            if raw is not None:
                ids[key] = uuid.UUID(str(raw))
        except ValueError:
            # Invalid ids are rejected by the route's own validation (422).
            continue
    return ids


async def _authorize(
    request: Request, user: User | None, use_case: AuthorizeWorkspaceAccess, role: WorkspaceRole
) -> WorkspaceMember | None:
    # No user means authentication is disabled or a trusted service is calling.
    if user is None:
        return None
    return await use_case.execute(
        AuthorizeWorkspaceAccessParams(user_id=user.id, required_role=role, **_path_ids(request))
    )


async def require_workspace_access(
    request: Request,
    user: User | None = Depends(get_current_user),
    use_case: AuthorizeWorkspaceAccess = Depends(authorize_workspace_access_factory),
) -> WorkspaceMember | None:
    # Reads need any membership; writes need at least the editor role.
    role = WorkspaceRole.VIEWER if request.method in READ_METHODS else WorkspaceRole.EDITOR
    return await _authorize(request, user, use_case, role)


async def require_workspace_member(
    request: Request,
    user: User | None = Depends(get_current_user),
    use_case: AuthorizeWorkspaceAccess = Depends(authorize_workspace_access_factory),
) -> WorkspaceMember | None:
    return await _authorize(request, user, use_case, WorkspaceRole.VIEWER)


async def require_workspace_owner(
    request: Request,
    user: User | None = Depends(get_current_user),
    use_case: AuthorizeWorkspaceAccess = Depends(authorize_workspace_access_factory),
) -> WorkspaceMember | None:
    return await _authorize(request, user, use_case, WorkspaceRole.OWNER)
