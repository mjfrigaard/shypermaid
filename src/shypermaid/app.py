"""App assembly and launch function."""

from __future__ import annotations

from pathlib import Path

from shiny import App, Inputs, Outputs, Session, ui
from shiny import run_app as _run_app

from .modules import editor_server, editor_ui, viewer_server, viewer_ui

WWW = Path(__file__).parent / "www"

MERMAID_JS = "shypermaid/vendor/mermaid.min.js"
PANZOOM_JS = "shypermaid/vendor/svg-pan-zoom.min.js"


def app_ui() -> ui.Tag:
    """Build the full page: editor sidebar, diagram viewer, and assets.

    Returns
    -------
    ui.Tag
        A fillable page with the Mermaid and svg-pan-zoom scripts, the
        package stylesheet, and the JavaScript binding in the page head.
    """
    return ui.page_fillable(
        ui.head_content(
            ui.tags.script(src=MERMAID_JS),
            ui.tags.script(src=PANZOOM_JS),
            ui.tags.link(rel="stylesheet", href="shypermaid/styles.css"),
            ui.tags.script(src="shypermaid/mermaid-binding.js"),
        ),
        ui.layout_sidebar(
            ui.sidebar(editor_ui("editor"), width=560, padding=0),
            viewer_ui("viewer"),
            border=False,
            border_radius=False,
            padding=0,
        ),
        padding=0,
        title="shypermaid",
    )


def server(input: Inputs, output: Outputs, session: Session) -> None:
    """Connect the editor module to the viewer module.

    Parameters
    ----------
    input, output, session
        Supplied by Shiny.
    """
    code = editor_server("editor")
    viewer_server("viewer", code=code)


def create_app() -> App:
    """Create the Shiny app and serve ``www/`` at ``/shypermaid``.

    Returns
    -------
    App
        The assembled Shiny app.
    """
    return App(app_ui(), server, static_assets={"/shypermaid": WWW})


app = create_app()


def run_app(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Launch the app and open it in a browser.

    Parameters
    ----------
    host
        Address to bind to.
    port
        Port to listen on.
    """
    if _run_app is None:  # shiny exports None under Pyodide
        raise RuntimeError("run_app() is not available in Pyodide")
    _run_app("shypermaid.app:app", host=host, port=port, launch_browser=True)
