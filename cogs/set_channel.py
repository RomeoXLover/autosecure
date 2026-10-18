"""Set Discord channel IDs for logging / hits."""

import json
import logging

import discord
from discord.ext import commands

log = logging.getLogger("bot")


def _alias() -> str:
    with open("config/bot.json") as f:
        return json.load(f)["enabled_commands"]["aliases"]["set_channel"]


class SetChannel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    set = discord.SlashCommandGroup(_alias())

    @set.command(name="channel", description="Sets your channel ID")
    async def set_channels(
        self,
        ctx: discord.ApplicationContext,
        choice: str = discord.Option(
            description="Choose channel type",
            choices=["Logs", "Logs (Censored)", "Hits"],
        ),
    ):
        if ctx.author.id not in self.bot.admins:
            await ctx.respond(
                "You do not have permission to execute this command!", ephemeral=True
            )
            return

        with open("config/config.json", "r") as f:
            new_config = json.load(f)

        match choice:
            case "Logs":
                new_config["discord"]["logs_channel"] = str(ctx.channel_id)
            case "Logs (Censored)":
                new_config["discord"]["censored_logs_channel"] = str(ctx.channel_id)
            case "Hits":
                new_config["discord"]["accounts_channel"] = str(ctx.channel_id)

        with open("config/config.json", "w") as f:
            json.dump(new_config, f, indent=4)

        await ctx.respond(f"Successfully set {choice} channel!", ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(SetChannel(bot))
