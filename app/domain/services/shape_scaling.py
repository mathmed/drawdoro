from typing import Any

from app.domain.services.canvas_geometry import CanvasRecord, shape_points

# Shapes whose size tldraw derives from props.scale: their w/h must stay as they are.
_SIZED_BY_SCALE = {"note", "text"}


# Scales a shape's own geometry in place, the way the editor's "scale" resize does: sizes and
# points grow, and so do stroke and label sizes (props.scale and the custom meta.fontSize).
def scale_shape(record: CanvasRecord, factor: float) -> None:
    if factor == 1:
        return
    props: dict[str, Any] = record.get("props") or {}
    _multiply(props, _scaled_props(record.get("type")), factor)
    for point in shape_points(record.get("type"), props):
        _multiply(point, ("x", "y"), factor)
    meta = record.get("meta")
    if isinstance(meta, dict):
        _multiply(meta, ("fontSize",), factor)


def _scaled_props(shape_type: object) -> tuple[str, ...]:
    if shape_type in _SIZED_BY_SCALE:
        return ("scale",)
    # Arrows have no size of their own: their points and bend are their geometry.
    if shape_type == "arrow":
        return ("scale", "bend")
    return ("scale", "w", "h")


def _multiply(values: dict[str, Any], keys: tuple[str, ...], factor: float) -> None:
    for key in keys:
        value = values.get(key)
        if isinstance(value, int | float) and not isinstance(value, bool):
            values[key] = value * factor
