"""AutoSecure Discord bot — entry point.

[context, OS, architecture]
Runtime: Python 3.12+, discord.py 2.0+ (py-cord fork)
Target: Linux x86_64 (also runs on Windows via start.ps1)
Purpose: Bot entrypoint; loads cogs, starts mail server, registers
         persistent views, syncs slash commands to guilds.
"""

import asyncio
import hashlib
import json
import logging
import os
import sys

import discord
from discord.ext import commands

from database.database import DBConnection
from mail.server import startServer
from ui.buttons.autobuy import AutobuyView
from ui.buttons.create_ticket import CreateTicketView
from ui.buttons.link_account import LinkAccountView


def _load_config() -> dict:
    with open("config/config.json", "r") as f:
        return json.load(f)


def _load_settings() -> dict:
    with open("config/bot.json", "r") as f:
        return json.load(f)


log = logging.getLogger("bot")

config = _load_config()
settings = _load_settings()


class DiscordBot(commands.Bot):
    """Main bot class with config-driven presence + fake-command generation."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix="!",
            case_insensitive=True,
            intents=intents,
            allowed_mentions=discord.AllowedMentions(
                roles=False, everyone=False, users=True
            ),
        )
        self.logger = log
        self.admins = list(map(int, config["owners"]))

        self.statuses: dict[str, discord.Status] = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible,
        }

        self.activities: dict[str, discord.ActivityType] = {
            "playing": discord.ActivityType.playing,
            "streaming": discord.ActivityType.streaming,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "competing": discord.ActivityType.competing,
        }

    async def build_command(self, name: str, description: str, response: str):
        """Register a fake slash command from config."""

        async def cog(ctx: discord.ApplicationContext):
            await ctx.response.send_message(response, ephemeral=True)

        cog.__name__ = name
        command = discord.SlashCommand(cog, name=name, description=description)
        self.add_application_command(command)

    def command_signature(self) -> str:
        payloads = []
        for cmd in self.pending_application_commands:
            try:
                payloads.append(cmd.to_dict())
            except Exception:
                payloads.append({"name": getattr(cmd, "name", "?")})
        blob = json.dumps(payloads, sort_keys=True, default=str)
        return hashlib.sha256(blob.encode()).hexdigest()

    async def on_ready(self):
        self.add_view(LinkAccountView())
        self.add_view(AutobuyView())
        self.add_view(CreateTicketView())
        self._startup_guild_sync_done = True

        presence = settings["presence"]
        activity = discord.Activity(
            type=self.activities[presence["activity_type"]],
            name=presence["activity_text"],
        )
        await self.change_presence(
            status=self.statuses[presence["status"]],
            activity=activity,
        )

        guild_ids = [guild.id for guild in self.guilds]
        await self.sync_commands(guild_ids=guild_ids)
        log.info(f"Synced commands to {len(guild_ids)} guild(s)")

    @staticmethod
    def setup_logging() -> None:
        root = logging.getLogger()
        root.setLevel(logging.INFO)

        file_handler = logging.FileHandler("logs/securing.log", mode="a")
        file_handler.setLevel(logging.INFO)
        root.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter("%(levelname)s | %(asctime)s | %(name)s | %(message)s")
        )

        bot_logger = logging.getLogger("bot")
        bot_logger.addHandler(console_handler)
        bot_logger.propagate = False

        for name in (
            "discord", "discord.http", "discord.gateway",
            "httpx", "mail.log", "mail.server",
        ):
            logging.getLogger(name).setLevel(logging.WARNING)

    async def load_cogs(self, directory: str = "./cogs") -> None:
        enabled_commands = settings["enabled_commands"]

        for file in os.listdir(directory):
            if file.endswith(".py"):
                cog_name = file[:-3]
                if enabled_commands["real"].get(cog_name):
                    self.load_extension(
                        f"{directory[2:].replace('/', '.')}.{cog_name}"
                    )
                    log.info(f"Loaded: {cog_name}")
            elif not (
                file in ["__pycache__", "utils", "buttons", "modals"]
                or file.endswith(("pyc", "txt"))
            ):
                await self.load_cogs(f"{directory}/{file}")

        for command in enabled_commands["fake"].keys():
            fake = enabled_commands["fake"][command]
            await self.build_command(
                name=fake["title"],
                description=fake["description"],
                response=fake["response"],
            )

        with DBConnection() as database:
            database.setup_tables()


asyncio.set_event_loop(asyncio.new_event_loop())
bot = DiscordBot()


async def main():
    async with bot:
        bot.remove_command("help")
        bot.setup_logging()
        startServer()
        await bot.load_cogs()
        await bot.start(config["tokens"]["bot_token"])


if __name__ == "__main__":
    asyncio.run(main())
