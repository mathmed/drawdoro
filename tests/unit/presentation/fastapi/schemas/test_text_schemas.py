import uuid

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from app.domain.constants.revisions import REVISION_SUMMARY_MAX_LENGTH
from app.presentation.fastapi.schemas.api_key_schemas import CreateApiKeyRequest
from app.presentation.fastapi.schemas.comment_schemas import CreateCommentRequest
from app.presentation.fastapi.schemas.diagram_schemas import (
    CreateDiagramRequest,
    UpdateDiagramRequest,
)
from app.presentation.fastapi.schemas.documentation_schemas import UpsertDocumentationPageRequest
from app.presentation.fastapi.schemas.folder_schemas import CreateFolderRequest, UpdateFolderRequest
from app.presentation.fastapi.schemas.gallery_schemas import (
    CreateGalleryItemRequest,
    InsertGalleryItemRequest,
    UpdateGalleryItemRequest,
)
from app.presentation.fastapi.schemas.project_schemas import (
    CreateProjectRequest,
    UpdateProjectRequest,
)
from app.presentation.fastapi.schemas.text_schemas import NulFreeStr
from app.presentation.fastapi.schemas.workspace_member_schemas import AddWorkspaceMemberRequest
from app.presentation.fastapi.schemas.workspace_schemas import (
    CreateWorkspaceRequest,
    UpdateWorkspaceRequest,
)

# Every request field whose text Postgres stores or looks up, with the other required fields.
TEXT_FIELDS: list[tuple[type[BaseModel], str, dict[str, object]]] = [
    (CreateWorkspaceRequest, "name", {"slug": "acme"}),
    (CreateWorkspaceRequest, "slug", {"name": "Acme"}),
    (UpdateWorkspaceRequest, "name", {"slug": "acme"}),
    (UpdateWorkspaceRequest, "slug", {"name": "Acme"}),
    (CreateProjectRequest, "name", {}),
    (CreateProjectRequest, "description", {"name": "Shop"}),
    (UpdateProjectRequest, "name", {}),
    (UpdateProjectRequest, "description", {"name": "Shop"}),
    (CreateFolderRequest, "name", {}),
    (UpdateFolderRequest, "name", {}),
    (CreateDiagramRequest, "name", {}),
    (UpdateDiagramRequest, "name", {}),
    (UpdateDiagramRequest, "revision_summary", {"name": "Flow"}),
    (UpsertDocumentationPageRequest, "content", {}),
    (CreateCommentRequest, "element_id", {"content": "Looks good"}),
    (CreateApiKeyRequest, "label", {}),
    (AddWorkspaceMemberRequest, "email", {}),
    (CreateGalleryItemRequest, "name", {"kind": "shapes"}),
    (CreateGalleryItemRequest, "description", {"name": "Box", "kind": "shapes"}),
    (UpdateGalleryItemRequest, "name", {}),
    (UpdateGalleryItemRequest, "description", {}),
    (InsertGalleryItemRequest, "revision_summary", {"item_id": str(uuid.uuid4())}),
]


@pytest.mark.parametrize(
    ("model", "field", "others"),
    TEXT_FIELDS,
    ids=[f"{model.__name__}.{field}" for model, field, _ in TEXT_FIELDS],
)
def test_should_drop_nul_characters_from_request_text(
    model: type[BaseModel], field: str, others: dict[str, object]
) -> None:
    request = model.model_validate(others | {field: "\x00Ca\x00fé\x00"})
    assert getattr(request, field) == "Café"


def test_should_keep_text_without_nul_as_it_is() -> None:
    text = " Tabs\tand\nnew lines, émojis 🚀 and \x01 other controls "
    assert TypeAdapter(NulFreeStr).validate_python(text) == text


def test_should_apply_length_limits_to_the_text_without_nul() -> None:
    longest = "x" * REVISION_SUMMARY_MAX_LENGTH + "\x00"
    request = UpdateDiagramRequest.model_validate({"name": "Flow", "revision_summary": longest})
    assert request.revision_summary == "x" * REVISION_SUMMARY_MAX_LENGTH
    with pytest.raises(ValidationError, match="string_too_short"):
        CreateApiKeyRequest.model_validate({"label": "\x00"})


def test_should_still_reject_values_that_are_not_text() -> None:
    with pytest.raises(ValidationError, match="string_type"):
        CreateFolderRequest.model_validate({"name": 5})


def test_should_document_nul_free_text_as_a_plain_string() -> None:
    assert TypeAdapter(NulFreeStr).json_schema() == TypeAdapter(str).json_schema()
