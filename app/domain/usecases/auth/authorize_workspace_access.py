import uuid

from app.domain.contracts.diagram_repository import DiagramRepository
from app.domain.contracts.folder_repository import FolderRepository
from app.domain.contracts.project_repository import ProjectRepository
from app.domain.contracts.usecase import InputData, Usecase
from app.domain.contracts.workspace_member_repository import WorkspaceMemberRepository
from app.domain.entities.models.workspace_member import WorkspaceMember
from app.domain.enums.workspace_role import WorkspaceRole
from app.domain.errors.domain_errors import ForbiddenError, NotFoundError


class AuthorizeWorkspaceAccessParams(InputData):
    user_id: uuid.UUID
    required_role: WorkspaceRole
    workspace_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    folder_id: uuid.UUID | None = None
    diagram_id: uuid.UUID | None = None


class AuthorizeWorkspaceAccess(Usecase[AuthorizeWorkspaceAccessParams, WorkspaceMember | None]):
    # Resolves the workspace behind any resource and checks the user's role in it. Resources
    # that don't belong to the given parents, or workspaces the user isn't in, are reported
    # as not found so their existence doesn't leak.
    def __init__(
        self,
        members: WorkspaceMemberRepository,
        projects: ProjectRepository,
        folders: FolderRepository,
        diagrams: DiagramRepository,
    ) -> None:
        self._members = members
        self._projects = projects
        self._folders = folders
        self._diagrams = diagrams

    async def execute(self, params: AuthorizeWorkspaceAccessParams) -> WorkspaceMember | None:
        workspace_id = await self._resolve_workspace(params)
        if workspace_id is None:
            return None
        member = await self._members.get(workspace_id, params.user_id)
        if member is None:
            raise NotFoundError("Workspace not found")
        if not member.role.includes(params.required_role):
            raise ForbiddenError(f"This action requires the {params.required_role} role")
        return member

    async def _resolve_workspace(self, params: AuthorizeWorkspaceAccessParams) -> uuid.UUID | None:
        project_id = await self._resolve_project(params)
        if project_id is None:
            return params.workspace_id
        project = await self._projects.get_by_id(project_id)
        if project is None or params.workspace_id not in (None, project.workspace_id):
            raise NotFoundError("Project not found")
        return project.workspace_id

    async def _resolve_project(self, params: AuthorizeWorkspaceAccessParams) -> uuid.UUID | None:
        project_id = params.project_id
        if params.diagram_id is not None:
            diagram = await self._diagrams.get_by_id(params.diagram_id)
            project_id = _expect_same(
                project_id, diagram.project_id if diagram else None, "Diagram"
            )
        if params.folder_id is not None:
            folder = await self._folders.get_by_id(params.folder_id)
            project_id = _expect_same(project_id, folder.project_id if folder else None, "Folder")
        return project_id


def _expect_same(expected: uuid.UUID | None, actual: uuid.UUID | None, kind: str) -> uuid.UUID:
    if actual is None or expected not in (None, actual):
        raise NotFoundError(f"{kind} not found")
    return actual
