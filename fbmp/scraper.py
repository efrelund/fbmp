from __future__ import annotations

import re
import urllib.parse

from playwright.sync_api import BrowserContext, Page

from fbmp import config


class LoginRequiredError(Exception):
    pass


def search_marketplace(
    context: BrowserContext,
    keyword: str,
    max_results: int | None = None,
    radius_km: int | None = None,
) -> list[dict]:
    """Search Facebook Marketplace and return listing dicts."""
    cfg = config.load()
    if max_results is None:
        max_results = cfg["max_results"]
    if radius_km is None:
        radius_km = cfg["radius_km"]

    page = context.new_page()
    try:
        return _do_search(page, keyword, max_results, radius_km=radius_km)
    finally:
        page.close()


def _do_search(page: Page, keyword: str, max_results: int, radius_km: int) -> list[dict]:
    query = urllib.parse.quote(keyword)
    url = f"https://www.facebook.com/marketplace/search/?query={query}&radius={radius_km}"
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


def _is_price(text: str) -> bool:
    """Check if a line looks like a price."""
    return bool(re.match(r"^[\$€£¥]", text) or text.lower() == "free")


def _parse_card_text(lines: list[str]) -> tuple[str, str, str]:
    """Parse card text lines into (title, price, location).

    Facebook cards show: price (or price range as two lines), title, location.
    Examples:
        ['$150', 'Couch', 'Fort Collins, CO']
        ['Free', '$50', 'Couch', 'Fort Collins, CO']
        ['$150', '$250', 'Navy blue couch', 'Fort Collins, CO']
    """
    if not lines:
        return "", "", ""

    # Consume price line(s) from the front
    idx = 0
    price_parts: list[str] = []
    while idx < len(lines) and _is_price(lines[idx]):
        price_parts.append(lines[idx])
        idx += 1

    price = " - ".join(price_parts) if price_parts else ""
    title = lines[idx] if idx < len(lines) else ""
    location = lines[idx + 1] if idx + 1 < len(lines) else ""

    return title, price, location


def parse_price_cents(price_str: str) -> int | None:
    """Extract the lowest numeric price in cents. Returns None if unparseable."""
    if not price_str or price_str.lower() == "free":
        return 0
    # Find all dollar amounts, take the first (lowest in a range)
    amounts = re.findall(r"\$[\d,]+(?:\.\d{2})?", price_str)
    if not amounts:
        return None
    raw = amounts[0].replace("$", "").replace(",", "")
    try:
        return int(float(raw) * 100)
    except ValueError:
        return None


def filter_by_price(
    listings: list[dict], min_price: int | None = None, max_price: int | None = None
) -> list[dict]:
    """Filter listings by price range (in dollars)."""
    if min_price is None and max_price is None:
        return listings
    result = []
    for item in listings:
        cents = parse_price_cents(item.get("price", ""))
        if cents is None:
            result.append(item)
            continue
        dollars = cents / 100
        if min_price is not None and dollars < min_price:
            continue
        if max_price is not None and dollars > max_price:
            continue
        result.append(item)
    return result
