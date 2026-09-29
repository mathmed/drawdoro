import base64
import uuid
from typing import Annotated, Protocol

from mcp.server.mcpserver import Image
from mcp.server.mcpserver.exceptions import ToolError
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import ViewportSize, sync_playwright
from pydantic import BaseModel, Field
from tools.api import DrawdoroApi, JsonObject

DEFAULT_MAX_SIZE = 1600
VIEWPORT: ViewportSize = {"width": 1280, "height": 800}
# The frontend's /render page defines this function once tldraw is mounted.
RENDER_FUNCTION = "window.drawdoroRender"
# Inside the cluster the frontend is plain http, which is not a secure context, so the browser
# leaves out crypto.randomUUID and the app fails on load. People always get https.
RANDOM_UUID_POLYFILL = """
if (typeof crypto.randomUUID !== "function") {
  crypto.randomUUID = () =>
    "10000000-1000-4000-8000-100000000000".replace(/[018]/g, (digit) =>
      (Number(digit) ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (Number(digit) / 4))))
        .toString(16)
    )
}
"""


class Region(BaseModel):
    x: float
    y: float
    width: Annotated[float, Field(gt=0)]
    height: Annotated[float, Field(gt=0)]


class RenderRequest(BaseModel):
    shape_ids: list[str] | None = None
    region: Region | None = None
    max_size: int = DEFAULT_MAX_SIZE


class Renderer(Protocol):
    def render(self, canvas_state: JsonObject, request: RenderRequest) -> bytes: ...


class BrowserRenderer:
    # Draws the canvas with the frontend itself, so custom shapes, fonts and label sizes come out
    # exactly as people see them in the editor.
    def __init__(self, frontend_url: str, timeout_seconds: float = 30) -> None:
        self._render_url = f"{frontend_url.rstrip('/')}/render"
        self._timeout_ms = timeout_seconds * 1000

    def render(self, canvas_state: JsonObject, request: RenderRequest) -> bytes:
        try:
            with sync_playwright() as playwright:
                # Container /dev/shm is tiny; Chromium crashes on big pages without this flag.
                browser = playwright.chromium.launch(args=["--disable-dev-shm-usage"])
                try:
                    page = browser.new_page(viewport=VIEWPORT)
                    page.add_init_script(RANDOM_UUID_POLYFILL)
                    page.goto(self._render_url, timeout=self._timeout_ms)
                    page.wait_for_function(
                        f"() => typeof {RENDER_FUNCTION} === 'function'", timeout=self._timeout_ms
                    )
                    encoded = page.evaluate(
                        f"([state, request]) => {RENDER_FUNCTION}(state, request)",
                        [canvas_state, request.model_dump(mode="json")],
                    )
                finally:
                    browser.close()
        except PlaywrightError as exc:
            raise ToolError(
                f"Could not render the diagram at {self._render_url}: {exc.message}"
            ) from exc
        return base64.b64decode(str(encoded))


class RenderTools:
    def __init__(self, api: DrawdoroApi, renderer: Renderer) -> None:
        self._api = api
        self._renderer = renderer

    def render_diagram(
        self,
        diagram_id: uuid.UUID,
        shape_ids: list[str] | None = None,
        region: Region | None = None,
        max_size: Annotated[int, Field(ge=200, le=4000)] = DEFAULT_MAX_SIZE,
    ) -> Image:
        """Render a diagram as a PNG, exactly as the editor draws it, to check how it looks.

        Use it after changing a diagram to catch overflowing labels, overlaps and misalignment.
        The whole canvas is scaled down so its longest side fits max_size; when text comes out
        too small to read, render a region or some shapes to zoom in.

        Args:
            diagram_id: Diagram to render.
            shape_ids: Render only these shapes (ids from get_diagram_outline); omit for all.
            region: Page area to render, in canvas coordinates (x, y, width, height); omit to fit
                the rendered shapes.
            max_size: Longest side of the image in pixels. Small canvases are never enlarged.
        """
        diagram = self._api.get_object(f"/diagrams/{diagram_id}")
        canvas_state = diagram.get("canvas_state")
        if not canvas_state:
            raise ToolError("The diagram has no canvas to render yet")
        request = RenderRequest(shape_ids=shape_ids, region=region, max_size=max_size)
        return Image(data=self._renderer.render(canvas_state, request), format="png")
