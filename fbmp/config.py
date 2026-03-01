import json
from pathlib import Path

FBMP_DIR = Path.home() / ".fbmp"
CONFIG_PATH = FBMP_DIR / "config.json"

DEFAULTS = {
    "profile_dir": str(FBMP_DIR / "chrome-profile"),
    "max_results": 20,
    "location": None,
}


def load() -> dict:
    config = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config.update(json.load(f))
    return config


def save(config: dict) -> None:
    FBMP_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def ensure_dirs() -> None:
    FBMP_DIR.mkdir(parents=True, exist_ok=True)
