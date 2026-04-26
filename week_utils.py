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
    chart_title: str  # full heading for leaderboard image (Week N - dates)


def current_week(*, tz_name: str) -> WeekBounds:
    tz = ZoneInfo(tz_name)
    today = datetime.now(tz).date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    human_start = f"{monday:%d %b %Y}"
    human_end = f"{sunday:%d %b %Y}"
    iso_week = monday.isocalendar()[1]
    return WeekBounds(
        start=str(monday),
        end=str(sunday),
        human_start=human_start,
        human_end=human_end,
        label=f"{monday:%d %b} – {sunday:%d %b %Y}",
        chart_title=f"Week {iso_week} - {human_start} ~ {human_end}",
    )
