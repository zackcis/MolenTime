"""Current calendar week (Mon–Sun) in the configured timezone."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


@dataclass
class WeekBounds:
    """Date range passed to WakaTime summaries API."""

    start: str  # YYYY-MM-DD
    end: str
    human_start: str
    human_end: str
    label: str  # short title for chart


def current_week(*, tz_name: str) -> WeekBounds:
    tz = ZoneInfo(tz_name)
    today = datetime.now(tz).date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return WeekBounds(
        start=str(monday),
        end=str(sunday),
        human_start=f"{monday:%d %b %Y}",
        human_end=f"{sunday:%d %b %Y}",
        label=f"{monday:%d %b} – {sunday:%d %b %Y}",
    )
