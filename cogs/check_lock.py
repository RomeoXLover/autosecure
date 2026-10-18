"""Check if a Microsoft account is locked or suspended."""

import json
import logging

from discord.ext import commands
import discord

from securing.auth.check_locked import check_locked

log = logging.getLogger("bot")


def _alias() -> str:
    with open("config/bot.json") as f:
        return json.load(f)["enabled_commands"]["aliases"]["check_lock"]


class CheckLock(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    check = discord.SlashCommandGroup(_alias())

    @check.command(name="locked", description="Checks if an account is locked")
    async def command(
        self,
        ctx: discord.ApplicationContext,
        email: discord.Option(str, "The email address to check"),
    ):
        if ctx.author.id not in self.bot.admins:
            await ctx.respond(
                "You do not have permission to execute this command!", ephemeral=True
            )
            return

        await ctx.defer(ephemeral=True)

        locked_info = await check_locked(email)

        if locked_info:
            status_code = locked_info.get("StatusCode")
            if status_code is not None and status_code != 500:
                value_raw = locked_info.get("Value")
                if value_raw:
                    try:
                        value_data = json.loads(value_raw)
                        status = value_data["status"]
                        if status.get("isAccountSuspended"):
                            await ctx.followup.send(
                                "This email is **suspended/locked**", ephemeral=True
                            )
                        elif status.get("isPhoneLocked"):
                            await ctx.followup.send(
                                "This email is **phone locked** "
                                "(requires phone verification to unlock)",
                                ephemeral=True,
                            )
                        else:
                            await ctx.followup.send(
                                "This email is **not** locked", ephemeral=True
                            )
                        return
                    except (KeyError, json.JSONDecodeError, TypeError):
                        pass

                await ctx.followup.send(
                    "This email is **locked**", ephemeral=True
                )
                return

        await ctx.followup.send(
            "Failed to check if this account is locked", ephemeral=True
        )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(CheckLock(bot))
