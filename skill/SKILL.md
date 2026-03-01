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
```
Returns only NEW listings (not previously seen). Add `--all` to skip dedup. Add `--json` for JSON output.

### Run all saved searches
```bash
uv run --project ~/code/fbmp fbmp run
```
Runs every saved search keyword and returns only new listings.

### Manage saved searches
```bash
uv run --project ~/code/fbmp fbmp add "kids bike"
uv run --project ~/code/fbmp fbmp remove "kids bike"
uv run --project ~/code/fbmp fbmp searches
```

## Interpreting output

The text output is ready to forward directly to the user. It looks like:
```
🔍 3 new listings for "couch"

$150 - Mid Century Modern Couch
📍 Vancouver, BC
🔗 https://facebook.com/marketplace/item/123456
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
