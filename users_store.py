"""Load coders and WakaTime API tokens from data/users.json."""

import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import config


def normalize_wakatime_basic_secret(token: str) -> str:
    """Value placed after ``Authorization: Basic ``.

    - Raw keys starting with ``waka_`` are Base64-encoded per current WakaTime API docs.
    - Otherwise the string is used as-is (e.g. LionBot / dashboard \"encoded\" Basic blob).
    """
    t = (token or "").strip()
    if not t or t.upper().startswith("PASTE_"):
        return ""
    if t.startswith("waka_"):
        return base64.b64encode(t.encode("utf-8")).decode("ascii")
    return t


@dataclass
class Coder:
    display_name: str
    wakatime_token: str  # Value for Authorization: Basic … (same as LionBot user.token)

    @classmethod
    def from_dict(cls, row: dict) -> "Coder":
        raw = str(row.get("wakatime_token", ""))
        return cls(
            display_name=str(row["display_name"]),
            wakatime_token=normalize_wakatime_basic_secret(raw),
        )


def _path() -> Path:
    return config.DATA_DIR / "users.json"


def _load_raw_rows() -> list[dict[str, Any]]:
    path = _path()
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        return []
    return [x for x in raw if isinstance(x, dict)]


def _save_raw_rows(rows: list[dict[str, Any]]) -> None:
    path = _path()
    with path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)


def load_coders() -> list[Coder]:
    return [c for x in _load_raw_rows() if (c := Coder.from_dict(x)).wakatime_token]


def upsert_coder_for_discord_user(
    *,
    discord_user_id: int,
    display_name: str,
    wakatime_token: str,
) -> None:
    """Create or update a coder entry keyed by Discord user id."""
    rows = _load_raw_rows()
    normalized = normalize_wakatime_basic_secret(wakatime_token)
    if not normalized:
        raise ValueError("wakatime token is empty or invalid")

    updated = False
    for row in rows:
        raw_user_id = row.get("discord_user_id")
        if str(raw_user_id).isdigit() and int(raw_user_id) == int(discord_user_id):
            row["display_name"] = display_name
            row["wakatime_token"] = normalized
            row["discord_user_id"] = int(discord_user_id)
            updated = True
            break

    if not updated:
        rows.append(
            {
                "display_name": display_name,
                "wakatime_token": normalized,
                "discord_user_id": int(discord_user_id),
            }
        )

    _save_raw_rows(rows)
