from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.usecases.documentation.get_documentation_page import GetDocumentationPage
from app.domain.usecases.documentation.upsert_documentation_page import UpsertDocumentationPage
from app.infra.database.repositories.documentation_page_repository import (
    DocumentationPageRepositoryImpl,
)
from app.infra.database.session import get_session


async def get_documentation_page_factory(
    session: AsyncSession = Depends(get_session),
) -> GetDocumentationPage:
    return GetDocumentationPage(DocumentationPageRepositoryImpl(session))


async def upsert_documentation_page_factory(
    session: AsyncSession = Depends(get_session),
) -> UpsertDocumentationPage:
    return UpsertDocumentationPage(DocumentationPageRepositoryImpl(session))
