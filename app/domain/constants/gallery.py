# Thumbnails are small PNG previews rendered by the client; anything bigger is not a thumbnail.
GALLERY_MAX_THUMBNAIL_BYTES = 256 * 1024
GALLERY_MAX_NAME_LENGTH = 255
# Tags make items findable by search; a short list of short words is all that takes.
GALLERY_MAX_TAGS = 10
GALLERY_MAX_TAG_LENGTH = 32
GALLERY_MAX_DESCRIPTION_LENGTH = 500
# Agents read gallery listings, so they stay short however large the gallery grows.
GALLERY_DEFAULT_LISTED_ITEMS = 50
GALLERY_MAX_LISTED_ITEMS = 200
