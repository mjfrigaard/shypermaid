from urllib.parse import urlparse

import pytest
from playwright.sync_api import Page, Route, expect
from shiny.pytest import create_app_fixture

app = create_app_fixture("e2e_app.py")

LOCAL = {"127.0.0.1", "localhost"}


@pytest.fixture
def offline(page: Page, app) -> tuple[Page, list[str]]:
    external: list[str] = []

    def block(route: Route) -> None:
        if urlparse(route.request.url).hostname in LOCAL:
            route.continue_()
        else:
            external.append(route.request.url)
            route.abort()

    page.route("**/*", block)
    page.goto(app.url)
    page.wait_for_selector(".sm-stage svg")
    return page, external


def test_renders_without_network(offline):
    page, external = offline
    expect(page.locator(".sm-error")).to_be_hidden()
    assert external == []


def test_elk_loads_without_network(offline):
    page, external = offline
    before = page.locator(".sm-stage svg").get_attribute("id")
    page.locator("#viewer-layout").select_option("elk")
    expect(page.locator(".sm-stage svg")).not_to_have_id(before, timeout=20000)
    expect(page.locator(".sm-error")).to_be_hidden()
    assert external == []


@pytest.mark.parametrize(
    "path",
    [
        "shymermaid/vendor/layout-elk/mermaid-layout-elk.esm.min.mjs",
        "shymermaid/vendor/layout-elk/chunks/mermaid-layout-elk.esm.min/render-GJFLM4CZ.mjs",
    ],
)
def test_mjs_served_as_javascript(page: Page, app, path: str):
    res = page.request.get(f"{app.url.rstrip('/')}/{path}")
    assert res.ok
    assert "javascript" in res.headers["content-type"]
