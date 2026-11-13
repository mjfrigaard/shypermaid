import functools
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from typing import Any

import pytest
from shiny import App as ShinyApp
from shiny import Inputs, Outputs, Session
from shiny.testserver import TestServerSession, test_server

from shypermaid import create_app
from shypermaid.diagram import DEFAULT_CODE, render_config
from shypermaid.modules import editor_server, viewer_server

EDITOR = {"code": DEFAULT_CODE, "auto": True, "render": 0}
VIEWER = {"theme": "default", "look": "classic", "layout": "dagre", "direction": "asis"}


def in_thread(fn: Callable[..., None]) -> Callable[..., None]:
    # test_server() runs its own event loop, which can't start on a thread
    # where Playwright's sync API already has one running.
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        with ThreadPoolExecutor(1) as pool:
            pool.submit(fn, *args, **kwargs).result()

    return wrapper


class App:
    def __init__(self) -> None:
        self.messages: list[tuple[str, dict[str, Any]]] = []

    def server(self, input: Inputs, output: Outputs, session: Session) -> None:
        async def record(type: str, message: dict[str, Any]) -> None:
            self.messages.append((type, message))

        session.send_custom_message = record  # type: ignore[method-assign]
        code = editor_server("editor")
        viewer_server("viewer", code=code)

    @property
    def last(self) -> dict[str, Any]:
        return self.messages[-1][1]


@contextmanager
def started(app: Callable[..., None] | ShinyApp) -> Iterator[TestServerSession]:
    with test_server(app) as ts:
        ts.make_scope("editor").set_inputs(**EDITOR)
        ts.make_scope("viewer").set_inputs(**VIEWER)
        yield ts


@pytest.fixture
def app():
    return App()


def editor(ts: TestServerSession, **kw: Any) -> None:
    ts.make_scope("editor").set_inputs(**kw)


def viewer(ts: TestServerSession, **kw: Any) -> None:
    ts.make_scope("viewer").set_inputs(**kw)


@in_thread
def test_sends_render_message(app: App):
    with started(app.server) as ts:
        assert ts.is_ok
    type_, msg = app.messages[-1]
    assert type_ == "shypermaid-render"
    assert msg["id"] == "viewer-canvas"
    assert msg["code"] == DEFAULT_CODE
    assert msg["config"] == render_config("default", "classic", "dagre")


@in_thread
def test_auto_update_sends_each_edit(app: App):
    with started(app.server) as ts:
        editor(ts, code="flowchart TD\n  a --> b")
    assert app.last["code"] == "flowchart TD\n  a --> b"


@in_thread
def test_manual_mode_waits_for_render(app: App):
    with started(app.server) as ts:
        editor(ts, auto=False)
        sent = len(app.messages)
        editor(ts, code="flowchart TD\n  a --> b")
        assert len(app.messages) == sent
        assert app.last["code"] == DEFAULT_CODE
        editor(ts, render=1)
        assert app.last["code"] == "flowchart TD\n  a --> b"


@in_thread
def test_turning_auto_back_on_commits_edits(app: App):
    with started(app.server) as ts:
        editor(ts, auto=False)
        editor(ts, code="flowchart LR\n  x --> y")
        editor(ts, auto=True)
    assert app.last["code"] == "flowchart LR\n  x --> y"


@pytest.mark.parametrize(
    "inputs,key,expected",
    [
        ({"theme": "dark"}, "theme", "dark"),
        ({"look": "handDrawn"}, "look", "handDrawn"),
        ({"layout": "elk"}, "layout", "elk"),
    ],
)
@in_thread
def test_menus_change_config(app: App, inputs, key, expected):
    with started(app.server) as ts:
        viewer(ts, **inputs)
    assert app.last["config"][key] == expected


@in_thread
def test_direction_rewrites_code(app: App):
    with started(app.server) as ts:
        viewer(ts, direction="LR")
    assert app.last["code"].startswith("flowchart LR\n")


@pytest.mark.filterwarnings("ignore:Error in Effect")
@in_thread
def test_unknown_menu_value_is_an_error(app: App):
    with started(app.server) as ts:
        viewer(ts, theme="neon")
        assert not ts.is_ok
        assert "Unknown theme" in (ts.error or "")


@in_thread
def test_app_server_wires_modules():
    with started(create_app()) as ts:
        assert ts.is_ok


@in_thread
def test_theme_note_empty_without_frontmatter_theme(app: App):
    with started(app.server) as ts:
        assert ts.make_scope("viewer").get_output("theme_note") == ""


@in_thread
def test_theme_note_shows_frontmatter_theme(app: App):
    with started(app.server) as ts:
        editor(ts, code="---\nconfig:\n  theme: forest\n---\nflowchart TD")
        note = ts.make_scope("viewer").get_output("theme_note")
        assert note == "Theme set in code: forest"
