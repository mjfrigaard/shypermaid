from shiny import App

from shymermaid import create_app
from shymermaid.app import WWW, app_ui


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


def test_static_assets_exist():
    assert (WWW / "mermaid-binding.js").is_file()
    assert (WWW / "styles.css").is_file()


def test_editor_has_highlight_layer():
    html = str(app_ui())
    assert 'class="sm-highlight"' in html
    assert 'class="sm-code"' in html


def test_viewer_has_download_buttons():
    html = str(app_ui())
    for action in ("download-svg", "download-png"):
        assert f'data-sm-action="{action}"' in html
