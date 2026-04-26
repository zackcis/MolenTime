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
    footer_time: str | None = None,
) -> Path:
    text_color = "white"
    background_color = "black"

    match template:
        case "top":
            ybottom = -0.5
            x = -1
            title = f"Molengeek — WakaTime  |  {week_label or ''}  |  {week_start or ''}  ~  {week_end or ''}"
            heading_code = f"ax.set_title({title!r}, pad=0, loc='center', va='top', fontsize=11, weight='bold', color=text_color)"
        case "bottom":
            ybottom = -1
            x = 0
            heading_code = (
                f"plt.figtext(.5, .1, {('Last update — ' + (footer_time or ''))!r}, "
                "fontsize=7.5, ha='center', color=text_color)"
            )
        case "middle":
            ybottom = -1
            x = 0
            heading_code = ""
        case _:
            raise ValueError(template)

    w = 785
    h = max(43, 43 * len(data))
    rows = len(data) + 2
    cols = 8

    fig, ax = plt.subplots(facecolor=background_color)
    fig.set_size_inches(w / 100, h / 100)
    ax.set_ylim(ybottom, rows)
    ax.set_xlim(0, cols)
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

    if heading_code:
        exec(heading_code, {"ax": ax, "plt": plt, "text_color": text_color})

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
    fig.savefig(out, format="png")
    plt.close(fig)
    return out
