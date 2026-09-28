from .comment_routes import router as comment_router
from .diagram_routes import router as diagram_router
from .documentation_routes import router as documentation_router
from .folder_routes import router as folder_router
from .health_routes import router as health_router
from .project_routes import router as project_router
from .websocket_routes import router as websocket_router
from .workspace_routes import router as workspace_router

routers = [
    health_router,
    workspace_router,
    project_router,
    folder_router,
    diagram_router,
    documentation_router,
    comment_router,
    websocket_router,
]
