"""Fetch weekly summaries from WakaTime for all coders (ported from LionBot)."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

import aiohttp

import config
from users_store import Coder


@dataclass
class WakaRow:
    """One row for the leaderboard table."""

    rank_cell: str
    coder: str
    total: str
    languages: str
    total_seconds: float

    def as_chart_row(self) -> dict:
        return {
            "": self.rank_cell,
            "Coder": self.coder,
            "Total": self.total,
            "Languages": self.languages,
        }


def _format_weekly_summary(coder_name: str, summary: dict | None) -> WakaRow | None:
    if summary is None:
        return None

    languages: dict[str, float] = {}
    for day in summary.get("data", []):
        for lang in day.get("languages", []):
            lang_name = lang["name"]
            languages.setdefault(lang_name, 0.0)
            languages[lang_name] += float(lang.get("total_seconds", 0))

    top = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:4]
    langs = ", ".join(name for name, _ in top)

    cum = summary.get("cumulative_total") or {}
    total_txt = (
        str(cum.get("text", "0s"))
        .replace(" hrs", "h")
        .replace(" mins", "min")
        .replace(" secs", "s")
    )
    total_seconds = float(cum.get("seconds", 0))

    is_zero = total_seconds == 0 or total_txt == "0s"
    return WakaRow(
        rank_cell="",
        coder=coder_name,
        total="0h 0min" if is_zero else total_txt,
        languages="" if is_zero else langs,
        total_seconds=total_seconds,
    )


async def _fetch_one(
    session: aiohttp.ClientSession,
    coder: Coder,
    *,
    start: str,
    end: str,
) -> tuple[bool, WakaRow | None]:
    """Returns (finished_this_coder, row). finished False means 429 — retry same coder."""
    url = f"{config.WAKATIME_API_URL}/users/current/summaries"
    headers = {
        "Authorization": f"Basic {coder.wakatime_token}",
        "Content-Type": "application/json",
    }
    params = {"start": start, "end": end}
    async with session.get(url, headers=headers, params=params) as response:
        if response.status == 429:
            print("[WakaTime] 429 Too Many Requests — will retry after buffer sleep")
            return False, None
        if response.status == 401:
            print(f"[WakaTime] 401 for {coder.display_name!r} — check wakatime_token in users.json")
            return True, None
        if response.status != 200:
            text = await response.text()
            print(f"[WakaTime] {response.status} for {coder.display_name!r}: {text[:200]}")
            return True, None
        data = await response.json()
        return True, _format_weekly_summary(coder.display_name, data)


async def fetch_all_weekly(
    coders: list[Coder],
    *,
    start: str,
    end: str,
) -> list[WakaRow]:
    """Mirror LionBot batching: on 429, sleep and retry remaining users."""
    if not coders:
        return []

    pending = list(coders)
    results: list[WakaRow] = []
    sleeped = 0.0
    t0 = time.time()

    while pending:
        async with aiohttp.ClientSession() as session:
            for coder in list(pending):
                done, row = await _fetch_one(session, coder, start=start, end=end)
                if not done:
                    break
                pending.remove(coder)
                if row is not None:
                    results.append(row)

        if pending:
            print(f"[WakaTime] rate limit buffer sleep {config.BUFFER_SLEEP_SECONDS}s")
            sleeped += float(config.BUFFER_SLEEP_SECONDS)
            await asyncio.sleep(config.BUFFER_SLEEP_SECONDS)

    results.sort(key=lambda r: r.total_seconds, reverse=True)
    for i, row in enumerate(results, start=1):
        row.rank_cell = str(i)
    print(f"[WakaTime] fetched {len(results)} coders in {time.time() - t0:.1f}s (sleep {sleeped:.1f}s)")
    return results


def merge_wakatime_results_with_coders(coders: list[Coder], fetched: list[WakaRow]) -> list[WakaRow]:
    """Ensure every registered coder appears; missing API rows become zero placeholders."""
    if not coders:
        return []
    by_name: dict[str, WakaRow] = {}
    for r in fetched:
        by_name.setdefault(r.coder, r)
    merged: list[WakaRow] = []
    for c in coders:
        hit = by_name.get(c.display_name)
        if hit is not None:
            merged.append(hit)
        else:
            merged.append(
                WakaRow(
                    rank_cell="",
                    coder=c.display_name,
                    total="0h 0min",
                    languages="",
                    total_seconds=0.0,
                )
            )
    merged.sort(key=lambda r: r.total_seconds, reverse=True)
    for i, row in enumerate(merged, start=1):
        row.rank_cell = str(i)
    if len(fetched) < len(coders):
        print(
            f"[WakaTime] showing {len(coders)} coders "
            f"({len(coders) - len(fetched)} without successful summary — zeros)"
        )
    return merged
