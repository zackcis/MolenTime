"""Load coders and WakaTime API tokens from data/users.json."""

import base64
import json
from dataclasses import dataclass
from pathlib import Path

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


def load_coders() -> list[Coder]:
    path = config.DATA_DIR / "users.json"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    if not isinstance(raw, list):
        return []
    return [c for x in raw if (c := Coder.from_dict(x)).wakatime_token]
