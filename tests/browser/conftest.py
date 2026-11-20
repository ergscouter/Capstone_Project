"""Run browser checks against a temporary local server and fresh browser data."""

import os
import sys
from pathlib import Path
from threading import Thread

import pytest
from werkzeug.serving import make_server

from app import create_app

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / ".test-artifacts"


@pytest.fixture(scope="session")
def live_app():
    server = make_server("127.0.0.1", 0, create_app(), threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=5)
    server.server_close()


@pytest.fixture(scope="session")
def browser():
    playwright = pytest.importorskip("playwright.sync_api")
    channel = os.environ.get(
        "EAGLE_EYE_BROWSER_CHANNEL", "msedge" if sys.platform == "win32" else "chromium"
    )
    options = {} if channel == "chromium" else {"channel": channel}
    with playwright.sync_playwright() as runner:
        instance = runner.chromium.launch(headless=True, timeout=20000, **options)
        yield instance
        instance.close()


@pytest.fixture
def context(browser):
    instance = browser.new_context(viewport={"width": 1280, "height": 900})
    yield instance
    instance.close()


@pytest.fixture
def page(context):
    instance = context.new_page()
    instance.set_default_timeout(10000)
    yield instance
    instance.close()


@pytest.fixture
def app_page(page, live_app):
    page.goto(live_app, wait_until="domcontentloaded")
    page.locator("#meeting-building:not([disabled])").wait_for()
    return page


@pytest.fixture
def artifact_dir():
    ARTIFACT_DIR.mkdir(exist_ok=True)
    return ARTIFACT_DIR
