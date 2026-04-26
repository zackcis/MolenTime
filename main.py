"""Entry point: Molengeek WakaTime leaderboard Discord bot."""

import config


def main() -> None:
    err = config.validate()
    if err:
        print(f"Config error: {err}")
        return

    from bot import build_bot

    bot = build_bot()
    bot.run(config.DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
