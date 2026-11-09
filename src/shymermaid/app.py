"""App assembly and launch function."""

from __future__ import annotations

from pathlib import Path

from shiny import App, Inputs, Outputs, Session, ui
from shiny._main import run_app as _run_app

from .modules import editor_server, editor_ui, viewer_server, viewer_ui

WWW = Path(__file__).parent / "www"

MERMAID_JS = "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"
PANZOOM_JS = "https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.2/dist/svg-pan-zoom.min.js"


def app_ui() -> ui.Tag:
    return ui.page_fillable(
        ui.head_content(
            ui.tags.script(src=MERMAID_JS),
            ui.tags.script(src=PANZOOM_JS),
            ui.tags.link(rel="stylesheet", href="shymermaid/styles.css"),
            ui.tags.script(src="shymermaid/mermaid-binding.js"),
        ),
        ui.layout_sidebar(
            ui.sidebar(editor_ui("editor"), width=560, padding=0),
            viewer_ui("viewer"),
            border=False,
            border_radius=False,
            padding=0,
        ),
        padding=0,
        title="shymermaid",
    )


def server(input: Inputs, output: Outputs, session: Session) -> None:
    code = editor_server("editor")
    viewer_server("viewer", code=code)


def create_app() -> App:
    return App(app_ui(), server, static_assets={"/shymermaid": WWW})


app = create_app()


def run_app(host: str = "127.0.0.1", port: int = 8000) -> None:
    _run_app("shymermaid.app:app", host=host, port=port, launch_browser=True)
