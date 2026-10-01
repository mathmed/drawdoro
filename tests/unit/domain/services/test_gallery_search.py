import pytest

from app.domain.entities.models.gallery_item import GalleryItemSummary
from app.domain.entities.objects.gallery_search import GallerySearch
from app.domain.enums.gallery_item_kind import GalleryItemKind
from app.domain.services.gallery_search import matches_gallery_search, search_gallery_items

LOGO = GalleryItemSummary(
    name="Temporal Logo",
    kind=GalleryItemKind.IMAGE,
    tags=["workflow", "orchestration"],
    description="Official mark, dark background",
)
CLUSTER = GalleryItemSummary(
    name="Cluster", kind=GalleryItemKind.SHAPES, tags=["kubernetes", "k8s"], description=None
)


@pytest.mark.parametrize(
    "text", [None, "", "   ", "temporal", "LOGO", "orchestr", "dark", "logo workflow"]
)
def test_should_match_words_in_name_description_or_tags(text: str | None) -> None:
    assert matches_gallery_search(LOGO, GallerySearch(text=text))


@pytest.mark.parametrize("text", ["kubernetes", "temporal kafka", "light"])
def test_should_need_every_word_to_match(text: str) -> None:
    assert not matches_gallery_search(LOGO, GallerySearch(text=text))


def test_should_filter_by_kind() -> None:
    assert matches_gallery_search(LOGO, GallerySearch(kind=GalleryItemKind.IMAGE))
    assert not matches_gallery_search(LOGO, GallerySearch(kind=GalleryItemKind.SHAPES))


@pytest.mark.parametrize("tag", ["k8s", " K8S "])
def test_should_filter_by_exact_tag_in_any_case(tag: str) -> None:
    assert matches_gallery_search(CLUSTER, GallerySearch(tag=tag))


def test_should_not_match_a_tag_by_prefix() -> None:
    assert not matches_gallery_search(CLUSTER, GallerySearch(tag="k8"))


def test_should_ignore_a_blank_tag() -> None:
    assert matches_gallery_search(CLUSTER, GallerySearch(tag="  "))


def test_should_combine_kind_tag_and_text() -> None:
    search = GallerySearch(text="cluster", kind=GalleryItemKind.SHAPES, tag="kubernetes")
    assert matches_gallery_search(CLUSTER, search)
    assert not matches_gallery_search(CLUSTER, GallerySearch(text="logo", tag="kubernetes"))


def test_should_keep_the_order_and_apply_the_limit() -> None:
    items = [LOGO, CLUSTER, LOGO]
    assert search_gallery_items(items, GallerySearch()) == items
    assert search_gallery_items(items, GallerySearch(), limit=2) == [LOGO, CLUSTER]
    assert search_gallery_items(items, GallerySearch(text="cluster"), limit=5) == [CLUSTER]
