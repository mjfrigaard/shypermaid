import pytest
from playwright.sync_api import Page
from shiny.pytest import create_app_fixture

from shypermaid.diagram import DIRECTIONS, set_direction

app = create_app_fixture("e2e_app.py")

DIAGRAMS = {
    "flowchart": "flowchart TD\n  a --> b\n  b --> c",
    "flowchart-elk": "flowchart-elk TD\n  a --> b\n  b --> c",
    "state": "stateDiagram-v2\n  [*] --> A\n  A --> B\n  B --> [*]",
    "state-composite": (
        "stateDiagram-v2\n  state S {\n    direction LR\n    x --> y\n  }\n  [*] --> S"
    ),
    "class": "classDiagram\n  A <|-- B\n  B <|-- C",
    "git": "gitGraph\n  commit\n  branch dev\n  commit\n  checkout main\n  commit",
}

RENDER = """async (code) => {
  mermaid.initialize({startOnLoad: false});
  try { await mermaid.render('sm-dir-' + Math.random().toString(36).slice(2), code);
        return 'ok'; }
  catch (e) { return String(e.message || e); }
}"""


@pytest.fixture(scope="module")
def mermaid_page(browser, app) -> Page:
    page = browser.new_page()
    page.goto(app.url)
    page.wait_for_selector(".sm-stage svg")
    yield page
    page.close()


@pytest.mark.parametrize("direction", [d for d in DIRECTIONS if d != "asis"])
@pytest.mark.parametrize("name", list(DIAGRAMS))
def test_rewritten_code_renders(mermaid_page: Page, name: str, direction: str):
    code = set_direction(DIAGRAMS[name], direction)
    assert mermaid_page.evaluate(RENDER, code) == "ok", code
