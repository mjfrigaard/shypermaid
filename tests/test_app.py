from shiny import App

from shypermaid import create_app
from shypermaid.app import WWW, app_ui


def test_create_app():
    assert isinstance(create_app(), App)


def test_ui_contains_modules():
    html = str(app_ui())
    for id_ in (
        "editor-code",
        "editor-auto",
        "viewer-theme",
        "viewer-layout",
        "viewer-canvas",
    ):
        assert f'id="{id_}"' in html


def test_tools_are_labeled_icons():
    import re

    html = str(app_ui())
    tools = re.findall(r'<button[^>]*class="sm-tool"[^>]*>.*?</button>', html, re.S)
    assert len(tools) == 7
    for tool in tools:
        assert "<svg" in tool
        assert re.search(r'aria-label="[^"]+"', tool)


def test_static_assets_exist():
    assert (WWW / "mermaid-binding.js").is_file()
    assert (WWW / "styles.css").is_file()


def test_vendored_libraries_exist():
    from shypermaid.app import MERMAID_JS, PANZOOM_JS

    for src in (MERMAID_JS, PANZOOM_JS):
        assert not src.startswith("http")
        assert (WWW / src.removeprefix("shypermaid/")).is_file()


def test_editor_has_highlight_layer():
    html = str(app_ui())
    assert 'class="sm-highlight"' in html
    assert 'class="sm-code"' in html


def test_viewer_has_download_buttons():
    html = str(app_ui())
    for action in ("download-svg", "download-png"):
        assert f'data-sm-action="{action}"' in html


def test_render_button_hidden_while_auto_update_on():
    html = str(app_ui())
    assert 'data-display-if="!input.auto"' in html
    assert 'data-ns-prefix="editor-"' in html
    assert 'id="viewer-theme_note"' in html
