# What the editor (tldraw) accepts on one page; more shapes and it refuses to load them.
CANVAS_MAX_SHAPES_PER_PAGE = 4000
# Space left between an inserted item and the shape or content it is placed next to.
CANVAS_DEFAULT_GAP = 80
# Far beyond anything people draw; keeps positions finite once moved and scaled.
CANVAS_MAX_COORDINATE = 1_000_000_000
# Inserted items can be scaled within these bounds.
CANVAS_MIN_SCALE = 0.1
CANVAS_MAX_SCALE = 10.0
# Index of the first shape on an empty page, as tldraw numbers them.
CANVAS_FIRST_INDEX = "a1"
# Size tldraw gives a shape whose size it computes itself (e.g. sticky notes), before scaling.
CANVAS_NOTE_SIZE = 200
CANVAS_FALLBACK_SIZE = 100
