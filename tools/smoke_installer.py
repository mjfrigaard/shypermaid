"""Launch an installed shypermaid desktop app and check that it works.

Usage: python tools/smoke_installer.py <app binary> <settings dir> <screenshot>

Starts the app with a remote debugging port, connects with Playwright,
renders a diagram, switches to the ELK layout, checks the parse error
message, and checks that the app wrote its settings folder.
"""

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

PORT = 9333
CODE = "flowchart TD\n  A[Start] --> B{Pick}\n  B --> C[Left]\n  B --> D[Right]"


def wait_for_app(proc, timeout=300):
    """Wait until the app window has loaded the Shiny app over HTTP."""
    end = time.time() + timeout
    while time.time() < end:
        if proc.poll() is not None:
            sys.exit(f"app exited early with code {proc.returncode}")
        try:
            url = f"http://127.0.0.1:{PORT}/json"
            with urllib.request.urlopen(url, timeout=2) as r:
                urls = [t["url"] for t in json.load(r) if t["type"] == "page"]
            if any(u.startswith("http") for u in urls):
                return
        except OSError:
            pass
        time.sleep(2)
    sys.exit("the app page did not load within 300s")


def app_page(browser):
    for context in browser.contexts:
        for page in context.pages:
            if page.url.startswith("http"):
                return page
    sys.exit("app page not found")


def main(binary, settings, shot):
    proc = subprocess.Popen([binary, f"--remote-debugging-port={PORT}"])
    try:
        wait_for_app(proc)
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")
            page = app_page(browser)
            print("app page:", page.url)

            stage = page.locator(".sm-stage svg")
            expect(stage).to_be_visible(timeout=60000)
            old = stage.get_attribute("id")
            page.locator(".sm-code textarea").fill(CODE)
            expect(stage).not_to_have_id(old, timeout=30000)
            print("render: ok")

            box = page.locator(".sm-stage svg g").first.bounding_box()
            page.locator("#viewer-layout").select_option("elk")
            page.wait_for_timeout(3000)
            expect(page.locator(".sm-error")).to_be_hidden()
            assert page.locator(".sm-stage svg g").first.bounding_box() != box
            print("elk layout: ok")

            page.locator(".sm-code textarea").fill("flowchart TD\n  A -->")
            expect(page.locator(".sm-error")).to_be_visible(timeout=10000)
            assert stage.count() == 1
            print("parse error keeps the diagram: ok")

            page.screenshot(path=shot)
            browser.close()
    finally:
        proc.terminate()

    if not Path(settings).is_dir():
        sys.exit(f"settings folder not found: {settings}")
    print("settings folder:", settings)


if __name__ == "__main__":
    main(*sys.argv[1:4])
