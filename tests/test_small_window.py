from playwright.sync_api import Page
from shiny.pytest import create_app_fixture

app = create_app_fixture("e2e_app.py")

STAGE_SIZE = """() => {
  const r = document.querySelector('.sm-stage').getBoundingClientRect();
  return [r.width, r.height];
}"""


def test_narrow_window_renders_without_error(page: Page, app) -> None:
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.set_viewport_size({"width": 500, "height": 400})
    page.goto(app.url)
    page.wait_for_selector(".sm-stage svg")
    page.select_option("select[id$='look']", "handDrawn")
    page.select_option("select[id$='layout']", "elk")
    page.wait_for_timeout(2000)
    width, height = page.evaluate(STAGE_SIZE)
    assert width > 0 and height > 0
    assert page.locator(".sm-error").is_hidden()
    page.set_viewport_size({"width": 1300, "height": 850})
    page.wait_for_timeout(1000)
    assert page.locator(".sm-error").is_hidden()
    assert errors == []
