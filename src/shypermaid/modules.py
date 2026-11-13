"""Shiny Core modules for the code editor and the diagram viewer."""

from __future__ import annotations

from faicons import icon_svg
from shiny import Inputs, Outputs, Session, module, reactive, render, ui
from shiny.module import resolve_id

from .diagram import (
    DEFAULT_CODE,
    DIRECTIONS,
    DOCS_URL,
    LAYOUTS,
    LOOKS,
    THEMES,
    code_theme,
    render_config,
    set_direction,
)


@module.ui
def editor_ui() -> ui.Tag:
    """Code editor with an Auto-Update switch and a Render button.

    The Render button shows only while Auto-Update is off.

    Call with a module id, as in ``editor_ui("editor")``.

    Returns
    -------
    ui.Tag
        The editor header and a text area with a syntax highlight layer.
    """
    return ui.div(
        ui.div(
            ui.span(icon_svg("code"), " Code", class_="sm-title"),
            ui.input_switch("auto", "Auto-Update", value=True),
            ui.panel_conditional(
                "!input.auto",
                ui.input_action_button("render", "Render", class_="btn-sm"),
            ),
            ui.a("Docs", href=DOCS_URL, target="_blank", class_="sm-docs"),
            class_="sm-editor-header",
        ),
        ui.div(
            ui.tags.pre(ui.tags.code(), class_="sm-highlight", aria_hidden="true"),
            ui.input_text_area(
                "code",
                None,
                value=DEFAULT_CODE,
                width="100%",
                spellcheck="false",
                autocomplete="off",
            ),
            class_="sm-code",
        ),
        ui.span(
            "Tab inserts spaces. Press Escape, then Tab, to leave the editor.",
            id=resolve_id("key_hint"),
            class_="sm-key-hint visually-hidden",
        ),
        class_="sm-editor",
    )


@module.server
def editor_server(
    input: Inputs, output: Outputs, session: Session
) -> reactive.Value[str]:
    """Track the Mermaid code the viewer should draw.

    With Auto-Update on, every edit is committed. With it off, code is
    committed only when Render is clicked. Call with the same id as
    `editor_ui()`, as in ``editor_server("editor")``.

    Returns
    -------
    reactive.Value[str]
        The committed Mermaid code.
    """
    committed: reactive.Value[str] = reactive.Value(DEFAULT_CODE)

    @reactive.effect
    def _auto() -> None:
        code = input.code()
        if input.auto():
            committed.set(code)

    @reactive.effect
    @reactive.event(input.render)
    def _manual() -> None:
        committed.set(input.code())

    return committed


def _tool(action: str, icon: str, label: str, target: str) -> ui.Tag:
    return ui.tags.button(
        icon_svg(icon),
        type="button",
        class_="sm-tool",
        title=label,
        aria_label=label,
        **{"data-sm-action": action, "data-sm-target": target},
    )


@module.ui
def viewer_ui() -> ui.Tag:
    """Diagram canvas with theme, look, layout, and direction menus and tools.

    Call with a module id, as in ``viewer_ui("viewer")``.

    Returns
    -------
    ui.Tag
        The toolbar, canvas, and tool buttons.
    """
    canvas = resolve_id("canvas")
    return ui.div(
        ui.div(
            ui.output_text("theme_note", inline=True),
            ui.input_select("theme", None, THEMES, width="auto"),
            ui.input_select("look", None, LOOKS, width="auto"),
            ui.input_select("layout", None, LAYOUTS, width="auto"),
            ui.input_select("direction", None, DIRECTIONS, width="auto"),
            class_="sm-toolbar",
        ),
        ui.div(
            ui.div(class_="sm-stage"),
            ui.div(class_="sm-error", hidden=True),
            id=canvas,
            class_="sm-canvas",
        ),
        ui.div(
            _tool("zoom-in", "magnifying-glass-plus", "Zoom in", canvas),
            _tool("zoom-out", "magnifying-glass-minus", "Zoom out", canvas),
            _tool("actual-size", "magnifying-glass", "Actual size", canvas),
            _tool("fit", "compress", "Fit", canvas),
            _tool("fullscreen", "expand", "Fullscreen", canvas),
            _tool("download-svg", "file-code", "Download SVG", canvas),
            _tool("download-png", "file-image", "Download PNG", canvas),
            class_="sm-tools",
        ),
        class_="sm-viewer",
    )


@module.server
def viewer_server(
    input: Inputs, output: Outputs, session: Session, code: reactive.Value[str]
) -> None:
    """Send the code and render options to the browser for drawing.

    Call with the same id as `viewer_ui()`, as in
    ``viewer_server("viewer", code=code)``.

    Parameters
    ----------
    code
        Mermaid code to draw, usually the value returned by
        `editor_server()`.
    """

    # The note is empty (hidden) most of the time; keep it updating anyway.
    @output(suspend_when_hidden=False)
    @render.text
    def theme_note() -> str:
        theme = code_theme(code())
        return f"Theme set in code: {theme}" if theme else ""

    @reactive.effect
    async def _render() -> None:
        await session.send_custom_message(
            "shypermaid-render",
            {
                "id": session.ns("canvas"),
                "code": set_direction(code(), input.direction()),
                "config": render_config(input.theme(), input.look(), input.layout()),
            },
        )
