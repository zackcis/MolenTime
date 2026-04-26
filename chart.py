"""Render leaderboard PNGs (style aligned with LionBot charts.leaderboard)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config


def render_leaderboard_png(
    template: str,
    image_alias: str,
    data: list[dict],
    *,
    week_label: str | None = None,
    week_start: str | None = None,
    week_end: str | None = None,
    chart_title: str | None = None,
    footer_time: str | None = None,
) -> Path:
    text_color = "white"
    background_color = "black"

    def _title_for_top() -> str:
        if chart_title and chart_title.strip():
            return chart_title.strip()
        if week_label and week_start and week_end:
            return f"{week_label}  -  {week_start}  ~  {week_end}"
        return (week_label or "").strip()

    match template:
        case "top":
            ybottom = -0.5
            x = -1
            title_top = _title_for_top()
            title_extra_px = 56
        case "bottom":
            ybottom = -1
            x = 0
            title_top = ""
            title_extra_px = 0
        case "middle":
            ybottom = -1
            x = 0
            title_top = ""
            title_extra_px = 0
        case _:
            raise ValueError(template)

    w = 785
    h = max(43, 43 * len(data)) + title_extra_px
    rows = len(data) + 2
    cols = 8

    fig, ax = plt.subplots(facecolor=background_color)
    fig.set_size_inches(w / 100, h / 100)
    ax.set_ylim(ybottom, rows)
    ax.set_xlim(0, cols)
    if template == "top":
        fig.subplots_adjust(left=0.04, right=0.96, bottom=0.06, top=0.78)
    else:
        fig.subplots_adjust(bottom=0.06, top=0.94)
    ax.axis("off")

    for index, user in enumerate(data[::-1]):
        for xpos, name in [
            (0.5, ""),
            (0.75, "Coder"),
            (2.875, "Total"),
            (4.25, "Languages"),
        ]:
            ax.text(
                x=xpos,
                y=index + 1 + x,
                s=user.get(name, ""),
                va="center",
                color=text_color,
                size=8.5 if name == "Coder" else 9.5,
                weight="bold" if name == "Coder" else "normal",
                ha="center" if name == "" else "left",
            )

    for xpos, name in [
        (0.5, ""),
        (0.75, "Coder"),
        (2.875, "Total"),
        (4.25, "Languages"),
    ]:
        ax.text(xpos, rows - 1 + x, name, weight="bold", size=11, color=text_color)

    if template == "top" and title_top:
        fig.suptitle(
            title_top,
            fontsize=15,
            fontweight="bold",
            color=text_color,
            y=0.96,
            va="top",
        )
    elif template == "bottom":
        plt.figtext(
            0.5,
            0.1,
            "Last update — " + (footer_time or ""),
            fontsize=7.5,
            ha="center",
            color=text_color,
        )

    ax.plot(
        [0.25, cols - 0.25],
        [rows - 1.375 + x, rows - 1.375 + x],
        ls="-",
        lw=1,
        c=text_color,
    )
    ax.plot([0.25, cols - 0.25], [0.5 + x, 0.5 + x], ls="-", lw=1, c=text_color)
    for index in range(len(data)):
        if index != 0:
            ax.plot(
                [0.25, cols - 0.2],
                [index + 0.5 + x, index + 0.5 + x],
                ls="-",
                lw=0.375,
                c=text_color,
            )

    out = config.STORAGE_IMAGES / f"{image_alias}_{template}_leaderboard.png"
    fig.savefig(
        out,
        format="png",
        facecolor=background_color,
        bbox_inches="tight",
        pad_inches=0.12,
    )
    plt.close(fig)
    return out
