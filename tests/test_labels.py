import pytest
from playwright.sync_api import Page
from shiny.pytest import create_app_fixture

app = create_app_fixture("e2e_app.py")

CODE = 'flowchart TD\n    a["<code>study.pdf</code>"] --> b["plain"]'

COLORS = """() => {
  const code = document.querySelector('.sm-stage foreignObject code');
  const label = code.parentElement;
  return [getComputedStyle(code).color, getComputedStyle(label).color];
}"""


@pytest.mark.parametrize("theme", ["default", "dark"])
def test_code_label_matches_label_color(page: Page, app, theme: str) -> None:
    page.goto(app.url)
    page.wait_for_selector(".sm-stage svg")
    page.locator("textarea").fill(CODE)
    page.select_option("select[id$='theme']", theme)
    page.wait_for_function(
        "document.querySelector('.sm-stage foreignObject code') !== null"
    )
    page.wait_for_timeout(500)
    code, label = page.evaluate(COLORS)
    assert code == label
