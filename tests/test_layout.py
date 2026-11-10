import pytest
from playwright.sync_api import Page, expect
from shiny.pytest import create_app_fixture

app = create_app_fixture("e2e_app.py")

CODE = "flowchart TD\n  a --> b\n  a --> c\n  b --> d\n  c --> d\n  d --> e"


@pytest.fixture
def viewer(page: Page, app) -> Page:
    page.goto(app.url)
    page.wait_for_selector(".sm-stage svg")
    page.locator(".sm-code textarea").fill(CODE)
    return page


def drawn(page: Page) -> str:
    return page.locator(".sm-stage svg").get_attribute("id")


def wait_for_redraw(page: Page, old_id: str) -> None:
    expect(page.locator(".sm-stage svg")).not_to_have_id(old_id, timeout=20000)


def elk_loaded(page: Page) -> bool:
    return page.evaluate(
        "() => performance.getEntriesByType('resource')"
        ".some(e => e.name.includes('layout-elk'))"
    )


def choose(page: Page, layout: str) -> None:
    before = drawn(page)
    page.locator("#viewer-layout").select_option(layout)
    wait_for_redraw(page, before)
    expect(page.locator(".sm-error")).to_be_hidden()


def test_layout_menu_defaults_to_dagre_without_loading_elk(viewer: Page):
    expect(viewer.locator("#viewer-layout")).to_have_value("dagre")
    assert not elk_loaded(viewer)


def test_elk_layout_loads_plugin_and_changes_layout(viewer: Page):
    dagre_box = viewer.locator(".sm-stage svg g").first.bounding_box()
    choose(viewer, "elk")
    assert elk_loaded(viewer)
    assert viewer.locator(".sm-stage svg g").first.bounding_box() != dagre_box


def test_back_to_dagre_after_elk(viewer: Page):
    choose(viewer, "elk")
    choose(viewer, "dagre")


def test_elk_load_failure_shows_error(viewer: Page):
    viewer.route("**/layout-elk@*/**", lambda route: route.abort())
    viewer.locator("#viewer-layout").select_option("elk")
    expect(viewer.locator(".sm-error")).to_contain_text("Could not load the ELK layout")
    expect(viewer.locator(".sm-stage svg")).to_be_visible()
