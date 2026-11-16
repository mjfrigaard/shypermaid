import pytest
from playwright.sync_api import Page
from shiny.pytest import create_app_fixture

app = create_app_fixture("e2e_app.py")

MENUS = ["#viewer-theme", "#viewer-look", "#viewer-layout", "#viewer-direction"]


def overlaps(a: dict, b: dict) -> bool:
    return not (
        a["x"] + a["width"] <= b["x"]
        or b["x"] + b["width"] <= a["x"]
        or a["y"] + a["height"] <= b["y"]
        or b["y"] + b["height"] <= a["y"]
    )


@pytest.mark.parametrize("size", [(800, 600), (1024, 650), (1400, 780)])
def test_toolbar_menus_fit(page: Page, app, size):
    page.set_viewport_size({"width": size[0], "height": size[1]})
    page.goto(app.url)
    page.wait_for_selector(".sm-stage svg")
    stage = page.locator(".sm-toolbar").locator("xpath=..").bounding_box()
    rail = page.locator(".sm-tools").bounding_box()
    for menu in MENUS:
        select = page.locator(menu)
        clipped = select.evaluate(
            "el => { const s = getComputedStyle(el);"
            " const pad = parseFloat(s.paddingLeft) + parseFloat(s.paddingRight);"
            " const c = document.createElement('canvas').getContext('2d');"
            " c.font = s.font;"
            " return c.measureText(el.selectedOptions[0].text).width"
            " > el.clientWidth - pad + 0.5; }"
        )
        assert not clipped, f"{menu} text is cut off at {size}"
        box = select.bounding_box()
        assert box["x"] >= stage["x"], f"{menu} spills left at {size}"
        assert not overlaps(box, rail), f"{menu} covers the tool rail at {size}"
