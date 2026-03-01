from __future__ import annotations

import json

import typer

from fbmp import config, store
from fbmp.browser import browser_context
from fbmp.scraper import LoginRequiredError, filter_by_price, search_marketplace

app = typer.Typer(help="Facebook Marketplace search CLI")


@app.command()
def login():
    """Open browser for manual Facebook login (persistent profile)."""
    config.ensure_dirs()
    typer.echo("Opening browser... Log into Facebook, then close the browser window.")
    with browser_context(headed=True) as ctx:
        page = ctx.new_page()
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        typer.echo("Waiting for you to log in. Close the browser when done.")
        # Wait until all pages are closed
        try:
            while ctx.pages:
                ctx.pages[0].wait_for_timeout(1000)
        except Exception:
            pass
    typer.echo("Login session saved.")


@app.command()
def search(
    keyword: str,
    all_listings: bool = typer.Option(False, "--all", help="Return all listings, skip dedup"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    headed: bool = typer.Option(False, "--headed", help="Show browser window"),
    max_results: int = typer.Option(0, "--max", help="Max results (0 = use config default)"),
    radius: int = typer.Option(0, "--radius", help="Search radius in km (0 = use config default)"),
    min_price: int = typer.Option(0, "--min-price", help="Min price in dollars (0 = no min)"),
    max_price: int = typer.Option(0, "--max-price", help="Max price in dollars (0 = no max)"),
):
    """Search Marketplace for a keyword."""
    config.ensure_dirs()
    cfg = config.load()
    mr = max_results if max_results > 0 else None
    rk = radius if radius > 0 else None
    mn = min_price or cfg.get("min_price")
    mx = max_price or cfg.get("max_price")
    try:
        with browser_context(headed=headed) as ctx:
            listings = search_marketplace(ctx, keyword, max_results=mr, radius_km=rk)
    except LoginRequiredError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None

    listings = filter_by_price(listings, min_price=mn, max_price=mx)

    if not all_listings:
        listings = store.filter_new(keyword, listings)

    _output(keyword, listings, output_json)


@app.command()
def searches():
    """List saved searches."""
    keywords = store.list_searches()
    if not keywords:
        typer.echo("No saved searches.")
        return
    for kw in keywords:
        typer.echo(kw)


@app.command()
def add(keyword: str):
    """Add a saved search."""
    store.add_search(keyword)
    typer.echo(f"Added: {keyword}")


@app.command()
def remove(keyword: str):
    """Remove a saved search."""
    if store.remove_search(keyword):
        typer.echo(f"Removed: {keyword}")
    else:
        typer.echo(f"Not found: {keyword}")


@app.command()
def clear(
    keyword: str = typer.Argument("", help="Clear seen listings for a keyword (all if empty)"),
    all_searches: bool = typer.Option(False, "--searches", help="Also remove all saved searches"),
):
    """Clear seen listings and optionally saved searches."""
    count = store.clear_seen(keyword or None)
    if keyword:
        typer.echo(f'Cleared {count} seen listings for "{keyword}".')
    else:
        typer.echo(f"Cleared {count} seen listings.")
    if all_searches:
        removed = store.clear_searches()
        typer.echo(f"Removed {removed} saved searches.")


@app.command()
def run(
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
    headed: bool = typer.Option(False, "--headed", help="Show browser window"),
    min_price: int = typer.Option(0, "--min-price", help="Min price in dollars (0 = no min)"),
    max_price: int = typer.Option(0, "--max-price", help="Max price in dollars (0 = no max)"),
):
    """Run all saved searches, output new listings only."""
    config.ensure_dirs()
    cfg = config.load()
    mn = min_price or cfg.get("min_price")
    mx = max_price or cfg.get("max_price")
    keywords = store.list_searches()
    if not keywords:
        typer.echo("No saved searches. Use 'fbmp add <keyword>' first.")
        raise typer.Exit(1)

    all_results = {}
    try:
        with browser_context(headed=headed) as ctx:
            for kw in keywords:
                try:
                    listings = search_marketplace(ctx, kw)
                    listings = filter_by_price(listings, min_price=mn, max_price=mx)
                    new_listings = store.filter_new(kw, listings)
                    if new_listings:
                        all_results[kw] = new_listings
                except LoginRequiredError as e:
                    typer.echo(str(e), err=True)
                    raise typer.Exit(1) from None
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    if output_json:
        typer.echo(json.dumps(all_results, indent=2))
        return

    if not all_results:
        typer.echo("No new listings.")
        return

    for kw, listings in all_results.items():
        _format_text(kw, listings)
        typer.echo("")


def _output(keyword: str, listings: list[dict], as_json: bool):
    if as_json:
        typer.echo(json.dumps(listings, indent=2))
        return
    if not listings:
        typer.echo(f'No new listings for "{keyword}".')
        return
    _format_text(keyword, listings)


def _format_text(keyword: str, listings: list[dict]):
    count = len(listings)
    typer.echo(f'\U0001f50d {count} new listing{"s" if count != 1 else ""} for "{keyword}"\n')
    for item in listings:
        price = item.get("price") or "N/A"
        title = item.get("title") or "Untitled"
        location = item.get("location") or ""
        listing_id = item.get("listing_id") or ""
        loc = f" · {location}" if location else ""
        typer.echo(f"{price} - {title}{loc}")
        if listing_id:
            typer.echo(f"fb://marketplace/item/{listing_id}")
            typer.echo(f"facebook.com/marketplace/item/{listing_id}")
