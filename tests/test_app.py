from shiny import App

from shymermaid import create_app
from shymermaid.app import WWW, app_ui


def test_create_app():
    assert isinstance(create_app(), App)


def test_ui_contains_modules():
    html = str(app_ui())
    for id_ in ("editor-code", "editor-auto", "viewer-theme", "viewer-canvas"):
        assert f'id="{id_}"' in html


def test_static_assets_exist():
    assert (WWW / "mermaid-binding.js").is_file()
    assert (WWW / "styles.css").is_file()
