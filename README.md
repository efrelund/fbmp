# fbmp - Facebook Marketplace Search CLI

Automated Facebook Marketplace keyword searches with dedup. Designed to be called by nanobot for Telegram notifications.

## Setup

```bash
git clone <repo-url> ~/code/fbmp
cd ~/code/fbmp
uv sync
uv run playwright install chromium
```

## First-time login

Open a browser to log into Facebook (session persists):

```bash
uv run fbmp login
```

## Usage

```bash
# Search (returns only new listings)
uv run fbmp search "mid century dresser"

# Search (all results, skip dedup)
uv run fbmp search "couch" --all

# JSON output
uv run fbmp search "couch" --json

# Manage saved searches
uv run fbmp add "kids bike"
uv run fbmp searches
uv run fbmp remove "kids bike"

# Run all saved searches
uv run fbmp run
```

## Mac Mini deployment

1. Clone and install (see Setup above)
2. Run `uv run fbmp login` and log into Facebook
3. Install the nanobot skill:
   ```bash
   mkdir -p ~/.nanobot/workspace/skills/fbmp
   ln -s ~/code/fbmp/skill/SKILL.md ~/.nanobot/workspace/skills/fbmp/SKILL.md
   ```
4. Test: `uv run fbmp search "test"`
5. Configure cron via nanobot CronTool for periodic `fbmp run`
