from __future__ import annotations

import re
import urllib.parse

from playwright.sync_api import BrowserContext, Page

from fbmp import config


class LoginRequiredError(Exception):
    pass


def search_marketplace(
    context: BrowserContext, keyword: str, max_results: int | None = None
) -> list[dict]:
    """Search Facebook Marketplace and return listing dicts."""
    cfg = config.load()
    if max_results is None:
        max_results = cfg["max_results"]

    page = context.new_page()
    try:
        return _do_search(page, keyword, max_results)
    finally:
        page.close()


def _do_search(page: Page, keyword: str, max_results: int) -> list[dict]:
    query = urllib.parse.quote(keyword)
    url = f"https://www.facebook.com/marketplace/search/?query={query}"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)

    # Check for login wall
    if _needs_login(page):
        raise LoginRequiredError("Facebook requires login. Run: fbmp login")

    # Wait for listings to appear
    page.wait_for_timeout(3000)

    listings = _extract_listings(page, max_results)

    # If we don't have enough, scroll once and try again
    if len(listings) < max_results:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        listings = _extract_listings(page, max_results)

    return listings[:max_results]


def _needs_login(page: Page) -> bool:
    """Detect if Facebook is showing a login wall."""
    # Check URL redirect to login
    if "/login" in page.url:
        return True
    # Check for login form
    login_form = page.query_selector('form[action*="login"]')
    if login_form:
        # But only if there are no marketplace listings visible
        listings = page.query_selector_all('a[href*="/marketplace/item/"]')
        if not listings:
            return True
    return False


def _extract_listings(page: Page, max_results: int) -> list[dict]:
    """Extract listing data from the current page."""
    listings = []
    seen_ids = set()

    # Find all marketplace listing links
    links = page.query_selector_all('a[href*="/marketplace/item/"]')

    for link in links:
        if len(listings) >= max_results:
            break

        href = link.get_attribute("href") or ""
        listing_id = _extract_listing_id(href)
        if not listing_id or listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)

        # Get the card container - walk up to find a reasonable parent
        card = link

        # Extract text content from the card
        text = card.inner_text()
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]

        title, price, location = _parse_card_text(lines)

        # Try to get thumbnail
        img = card.query_selector("img")
        thumbnail = img.get_attribute("src") if img else None

        listing_url = f"https://www.facebook.com/marketplace/item/{listing_id}/"

        listings.append(
            {
                "listing_id": listing_id,
                "title": title,
                "price": price,
                "location": location,
                "url": listing_url,
                "thumbnail": thumbnail,
            }
        )

    return listings


def _extract_listing_id(href: str) -> str | None:
    """Pull the numeric listing ID from a marketplace URL."""
    match = re.search(r"/marketplace/item/(\d+)", href)
    return match.group(1) if match else None


def _parse_card_text(lines: list[str]) -> tuple[str, str, str]:
    """Parse card text lines into (title, price, location).

    Facebook card text typically has: price, title, location, distance
    but order can vary. We use heuristics.
    """
    price = ""
    title = ""
    location = ""

    for line in lines:
        # Price detection: starts with $ or currency-like patterns, or "Free"
        if not price and (re.match(r"^[\$€£¥C]", line) or line.lower() == "free"):
            price = line
        elif not title and price:
            # First non-price line after price is usually the title
            title = line
        elif not location and title:
            # Next line is usually location
            location = line

    # Fallback: if no price found, first line is title
    if not title and lines:
        title = lines[0]
        if len(lines) > 1:
            location = lines[1]

    return title, price, location
