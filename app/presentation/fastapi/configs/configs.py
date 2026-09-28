from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.presentation.fastapi.routes as routes
from app.common.settings import Settings
from app.presentation.fastapi.dependencies.current_user import get_current_user
from app.presentation.fastapi.handlers.domain_error_handler import register_error_handlers
from app.presentation.fastapi.middlewares.request_logging_middleware import (
    request_logging_middleware,
)


def apply_routes_config(app: FastAPI) -> None:
    for router in routes.public_routers:
        app.include_router(router)
    for router in routes.protected_routers:
        app.include_router(router, dependencies=[Depends(get_current_user)])


def make_fastapi_app(settings: Settings) -> FastAPI:
    if settings.is_production and not settings.auth_enabled:
        raise RuntimeError("AUTH_ENABLED must be true in production")
    app = FastAPI(
        title=settings.app_name,
        description="Architecture diagramming and documentation tool.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(request_logging_middleware)

    register_error_handlers(app)
    apply_routes_config(app)
    return app
