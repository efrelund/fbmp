---
name: fbmp
description: Search Facebook Marketplace for listings and manage saved searches.
metadata: {"nanobot":{"emoji":"🛒","requires":{"bins":["uv"]}}}
---

# Facebook Marketplace Search

Search Facebook Marketplace and return new listings with dedup.

## Commands

Run all commands via ExecTool with: `uv run --project ~/code/fbmp fbmp <command>`

### On-demand search
```bash
uv run --project ~/code/fbmp fbmp search "mid century dresser"
uv run --project ~/code/fbmp fbmp search "dresser" --min-price 50 --max-price 300
```
Returns only NEW listings (not previously seen).
Options: `--all` (skip dedup), `--json`, `--min-price N`, `--max-price N` (dollars), `--radius N` (km).

### Run all saved searches
```bash
uv run --project ~/code/fbmp fbmp run
uv run --project ~/code/fbmp fbmp run --min-price 10
```
Runs every saved search keyword and returns only new listings. Supports `--min-price` and `--max-price`.

### Manage saved searches
```bash
uv run --project ~/code/fbmp fbmp add "kids bike"
uv run --project ~/code/fbmp fbmp remove "kids bike"
uv run --project ~/code/fbmp fbmp searches
```

### Reset / clear
```bash
uv run --project ~/code/fbmp fbmp clear                  # clear all seen listings (re-triggers dedup)
uv run --project ~/code/fbmp fbmp clear "couch"           # clear seen for one keyword only
uv run --project ~/code/fbmp fbmp clear --searches        # clear seen + remove all saved searches
```

## Interpreting output

The text output is ready to forward directly to the user. It includes deep links (fb://) for the Facebook app and web links as fallback:
```
🔍 2 new listings for "couch"

$150 - Mid Century Couch · Fort Collins, CO
fb://marketplace/item/123456
facebook.com/marketplace/item/123456
```

"No new listings" means dedup filtered everything — nothing new since last check.

## Scheduling

Use CronTool to run `uv run --project ~/code/fbmp fbmp run` on a schedule (e.g. every 2 hours). Forward any output to the user.

## When to use

- User asks to "search marketplace", "find on Facebook Marketplace", "check marketplace for X"
- For on-demand: use `fbmp search "<keyword>"`
- For recurring monitoring: use `fbmp add "<keyword>"` then schedule `fbmp run`

## Troubleshooting

If you see "Facebook requires login", tell the user to run `fbmp login` on the Mac Mini to authenticate the browser session.
