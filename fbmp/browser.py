from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import sync_playwright

from fbmp import config

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@contextmanager
def browser_context(headed: bool = False):
    """Yield a Playwright BrowserContext with persistent login profile."""
    cfg = config.load()
    profile_dir = cfg["profile_dir"]
    Path(profile_dir).mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=not headed,
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )
        try:
            yield context
        finally:
            context.close()
