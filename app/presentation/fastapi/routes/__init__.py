from .auth_routes import router as auth_router
from .comment_routes import router as comment_router
from .diagram_routes import router as diagram_router
from .documentation_routes import router as documentation_router
from .folder_routes import router as folder_router
from .health_routes import router as health_router
from .project_routes import router as project_router
from .share_routes import public_router as public_share_router
from .share_routes import router as share_router
from .websocket_routes import router as websocket_router
from .workspace_member_routes import router as workspace_member_router
from .workspace_routes import router as workspace_router

# Reachable without a signed-in user: health checks, and the WebSocket, which
# authenticates itself from the ?token= query parameter.
public_routers = [health_router, websocket_router, public_share_router]

protected_routers = [
    auth_router,
    workspace_router,
    workspace_member_router,
    project_router,
    folder_router,
    diagram_router,
    documentation_router,
    comment_router,
    share_router,
]
