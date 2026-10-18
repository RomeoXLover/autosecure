"""Placeholder cog — 'goon' test command."""

import json
import logging

import discord
from discord.ext import commands

log = logging.getLogger("bot")


def _alias() -> str:
    with open("config/bot.json") as f:
        return json.load(f)["enabled_commands"]["aliases"]["goon"]


class Goon(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.slash_command(name=_alias(), description="goons")
    async def code_command(self, ctx: discord.ApplicationContext):
        await ctx.response.send_message("goon", ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Goon(bot))
