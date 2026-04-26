"""Persist Discord message IDs so leaderboard images are edited in place."""

import json
from pathlib import Path

import config


def _path() -> Path:
    return config.DATA_DIR / "leaderboard_messages.json"


def load_message_ids() -> dict[str, int | None]:
    path = _path()
    if not path.exists():
        return {"top": None, "middle": None, "bottom": None}
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    out = {"top": None, "middle": None, "bottom": None}
    for key in out:
        v = data.get(key)
        out[key] = int(v) if v is not None else None
    return out


def save_message_ids(ids: dict[str, int | None]) -> None:
    path = _path()
    with path.open("w", encoding="utf-8") as f:
        json.dump(ids, f, indent=2)
