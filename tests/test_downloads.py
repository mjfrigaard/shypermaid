import base64
import math
import re
import struct

import pytest
from playwright.sync_api import Page
from shiny.pytest import create_app_fixture

app = create_app_fixture("e2e_app.py")

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@pytest.fixture
def viewer(page: Page, app) -> Page:
    page.goto(app.url)
    page.wait_for_selector(".sm-stage svg")
    return page


def download(page: Page, label: str) -> tuple[bytes, str]:
    with page.expect_download() as info:
        page.get_by_role("button", name=f"Download {label}").click()
    return info.value.path().read_bytes(), info.value.suggested_filename


def png_size(data: bytes) -> tuple[int, int]:
    return struct.unpack(">II", data[16:24])


def view_box(svg: bytes) -> tuple[float, float]:
    m = re.search(rb'viewBox="[-\d.]+ [-\d.]+ ([\d.]+) ([\d.]+)"', svg)
    assert m
    return float(m[1]), float(m[2])


def png_pixels(page: Page, data: bytes) -> dict:
    return page.evaluate(
        """async (b64) => {
          const img = new Image();
          img.src = 'data:image/png;base64,' + b64;
          await img.decode();
          const c = document.createElement('canvas');
          c.width = img.width; c.height = img.height;
          const ctx = c.getContext('2d');
          ctx.drawImage(img, 0, 0);
          const px = ctx.getImageData(0, 0, c.width, c.height).data;
          const bg = Array.from(px.slice(0, 4));
          let other = 0;
          for (let i = 0; i < px.length; i += 4) {
            if (px[i] !== bg[0] || px[i + 1] !== bg[1] || px[i + 2] !== bg[2]) other++;
          }
          return {corner: bg, share: other / (px.length / 4)};
        }""",
        base64.b64encode(data).decode(),
    )


def test_svg_download(viewer: Page):
    data, name = download(viewer, "SVG")
    assert name == "diagram.svg"
    assert data.lstrip().startswith(b"<svg")
    assert b"foreignObject" in data


def test_png_download_is_png_at_twice_the_diagram_size(viewer: Page):
    data, name = download(viewer, "PNG")
    assert name == "diagram.png"
    assert data.startswith(PNG_SIGNATURE)
    w, h = view_box(download(viewer, "SVG")[0])
    assert png_size(data) == (math.ceil(w * 2), math.ceil(h * 2))


def test_png_has_white_background_and_drawing(viewer: Page):
    data, _ = download(viewer, "PNG")
    px = png_pixels(viewer, data)
    assert px["corner"] == [255, 255, 255, 255]
    assert px["share"] > 0.02


def test_png_dark_theme_background(viewer: Page):
    viewer.locator("#viewer-theme").select_option("dark")
    viewer.wait_for_timeout(500)
    data, _ = download(viewer, "PNG")
    assert png_pixels(viewer, data)["corner"] == [51, 51, 51, 255]


LABELS = (
    "flowchart TD\n"
    '    a[/"<code>study.extract.json</code>"/] --> b[("<code>corpus.sqlite</code>")]'
)

OVERFLOW = """() => Array.from(document.querySelectorAll('foreignObject')).map(fo => {
  const label = fo.firstElementChild;
  return label.scrollWidth - fo.width.baseVal.value;
})"""


def test_svg_code_labels_fit_when_opened_alone(viewer: Page):
    viewer.locator("textarea").fill(LABELS)
    viewer.wait_for_function(
        "document.querySelector('.sm-stage foreignObject code') !== null"
    )
    viewer.wait_for_timeout(500)
    data, _ = download(viewer, "SVG")
    alone = viewer.context.new_page()
    alone.set_content(data.decode())
    overflow = alone.evaluate(OVERFLOW)
    assert overflow
    assert max(overflow) <= 1
