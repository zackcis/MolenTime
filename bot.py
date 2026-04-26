"""Discord bot: periodic WakaTime leaderboard images for Molengeek."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

import config
import chart
import state_store
import week_utils
from users_store import load_coders, upsert_coder_for_discord_user
from wakatime_client import fetch_all_weekly, merge_wakatime_results_with_coders


def _split_thirds(rows: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    n = len(rows)
    if n == 0:
        return [], [], []
    a = n // 3
    b = 2 * n // 3
    return rows[:a], rows[a:b], rows[b:]


class MolengeekLeaderboardBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await self.tree.sync()

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} ({self.user.id})")
        if not self.update_leaderboard_loop.is_running():
            self.update_leaderboard_loop.change_interval(
                minutes=max(1, config.UPDATE_INTERVAL_MINUTES)
            )
            self.update_leaderboard_loop.start()

    async def update_leaderboard_once(self) -> list[Path]:
        coders = load_coders()
        if not coders:
            print("[Leaderboard] data/users.json is empty or missing tokens — nothing to post")
            return []

        week = week_utils.current_week(tz_name=config.TIMEZONE)
        fetched = await fetch_all_weekly(
            coders,
            start=week.start,
            end=week.end,
        )
        rows = merge_wakatime_results_with_coders(coders, fetched)
        if not fetched:
            print("[Leaderboard] no successful WakaTime responses — all coders shown as 0h 0min")
        table = [r.as_chart_row() for r in rows]

        # For small leaderboards, post a single clean image.
        if len(table) < 9:
            top_rows, mid_rows, bot_rows = table, [], []
        else:
            top_rows, mid_rows, bot_rows = _split_thirds(table)
        now = datetime.now(ZoneInfo(config.TIMEZONE))
        time_footer = f"{now:%A %d %b %I:%M %p}".replace("AM", "am").replace("PM", "pm")

        chart.render_leaderboard_png(
            "top",
            "global",
            top_rows,
            week_label=week.label,
            week_start=week.human_start,
            week_end=week.human_end,
            chart_title=week.chart_title,
        )
        if mid_rows:
            chart.render_leaderboard_png("middle", "global", mid_rows)
        if bot_rows:
            chart.render_leaderboard_png(
                "bottom",
                "global",
                bot_rows,
                footer_time=time_footer,
            )

        rendered_paths: list[Path] = [config.STORAGE_IMAGES / "global_top_leaderboard.png"]
        if mid_rows:
            rendered_paths.append(config.STORAGE_IMAGES / "global_middle_leaderboard.png")
        if bot_rows:
            rendered_paths.append(config.STORAGE_IMAGES / "global_bottom_leaderboard.png")

        channel = self.get_channel(config.LEADERBOARD_CHANNEL_ID)
        if channel is None or not isinstance(channel, discord.TextChannel):
            print("[Leaderboard] LEADERBOARD_CHANNEL_ID not found or not a text channel")
            return rendered_paths

        ids = state_store.load_message_ids()
        positions_to_post = ["top"]
        if mid_rows:
            positions_to_post.append("middle")
        if bot_rows:
            positions_to_post.append("bottom")

        for position in positions_to_post:
            path = config.STORAGE_IMAGES / f"global_{position}_leaderboard.png"
            file = discord.File(path, filename=f"{position}_leaderboard.png")
            msg_id = ids.get(position)

            try:
                if msg_id is not None:
                    msg = await channel.fetch_message(msg_id)
                    await msg.edit(content="", attachments=[file])
                else:
                    msg = await channel.send(file=file)
                    ids[position] = msg.id
            except discord.NotFound:
                msg = await channel.send(file=file)
                ids[position] = msg.id

        # Remove previously created extra panels when we are in single-image mode.
        for stale_position in ("middle", "bottom"):
            if stale_position in positions_to_post:
                continue
            stale_id = ids.get(stale_position)
            if stale_id is None:
                continue
            try:
                stale_msg = await channel.fetch_message(stale_id)
                await stale_msg.delete()
            except discord.NotFound:
                pass
            ids[stale_position] = None

        state_store.save_message_ids(ids)
        print(f"[Leaderboard] updated #{channel.name} ({channel.id})")
        return rendered_paths

    @tasks.loop(minutes=15)
    async def update_leaderboard_loop(self) -> None:
        try:
            await self.update_leaderboard_once()
        except Exception as e:
            print(f"[Leaderboard] error: {type(e).__name__}: {e}")

    @update_leaderboard_loop.before_loop
    async def _before_leaderboard_loop(self) -> None:
        await self.wait_until_ready()

    async def close(self) -> None:
        self.update_leaderboard_loop.cancel()
        await super().close()


bot_instance: MolengeekLeaderboardBot | None = None


def build_bot() -> MolengeekLeaderboardBot:
    global bot_instance
    bot_instance = MolengeekLeaderboardBot()

    @bot_instance.tree.command(name="refresh_leaderboard", description="Post/update WakaTime leaderboard now")
    async def refresh_leaderboard(interaction: discord.Interaction) -> None:
        allowed = (
            interaction.user.id in config.ADMIN_USER_IDS
            if config.ADMIN_USER_IDS
            else bool(
                getattr(interaction.user, "guild_permissions", None)
                and interaction.user.guild_permissions.administrator
            )
        )
        if not allowed:
            await interaction.response.send_message(
                "You need Administrator or be listed in ADMIN_USER_IDS.", ephemeral=True
            )
            return
        await interaction.response.defer(ephemeral=True)
        assert bot_instance is not None
        paths = await bot_instance.update_leaderboard_once()
        files = [discord.File(p, filename=p.name) for p in paths]
        if files:
            await interaction.followup.send(
                "Leaderboard updated.",
                ephemeral=True,
                files=files,
            )
        else:
            await interaction.followup.send(
                "Nothing to show — add coders (e.g. `/register_wakatime`) or check `users.json`.",
                ephemeral=True,
            )

    @bot_instance.tree.command(
        name="register_wakatime",
        description="Register or update your WakaTime token for this leaderboard",
    )
    async def register_wakatime(
        interaction: discord.Interaction,
        wakatime_token: str,
        display_name: str | None = None,
    ) -> None:
        chosen_name = (display_name or interaction.user.display_name).strip()
        if not chosen_name:
            chosen_name = interaction.user.name
        try:
            upsert_coder_for_discord_user(
                discord_user_id=interaction.user.id,
                display_name=chosen_name,
                wakatime_token=wakatime_token,
            )
        except ValueError:
            await interaction.response.send_message(
                "Invalid token. Provide a `waka_...` key or encoded Basic secret.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "Saved your WakaTime token. Run `/refresh_leaderboard` to post now.",
            ephemeral=True,
        )

    return bot_instance
