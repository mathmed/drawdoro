from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.usecases.template.create_template import CreateTemplate
from app.domain.usecases.template.delete_template import DeleteTemplate
from app.domain.usecases.template.get_template import GetTemplate
from app.domain.usecases.template.list_templates import ListTemplates
from app.infra.database.repositories.template_repository import TemplateRepositoryImpl
from app.infra.database.session import get_session


async def create_template_factory(session: AsyncSession = Depends(get_session)) -> CreateTemplate:
    return CreateTemplate(TemplateRepositoryImpl(session))


async def get_template_factory(session: AsyncSession = Depends(get_session)) -> GetTemplate:
    return GetTemplate(TemplateRepositoryImpl(session))


async def list_templates_factory(session: AsyncSession = Depends(get_session)) -> ListTemplates:
    return ListTemplates(TemplateRepositoryImpl(session))


async def delete_template_factory(session: AsyncSession = Depends(get_session)) -> DeleteTemplate:
    return DeleteTemplate(TemplateRepositoryImpl(session))
