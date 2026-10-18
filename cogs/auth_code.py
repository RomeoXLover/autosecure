"""Generate TOTP codes for authenticator secrets."""

import json
import logging

import discord
from discord.ext import commands

from shared.gen_totp import totp
from ui.buttons.totp_refresh import ButtonTOTP

log = logging.getLogger("bot")


def _alias() -> str:
    with open("config/bot.json") as f:
        return json.load(f)["enabled_commands"]["aliases"]["auth_code"]


class AuthCode(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    auth = discord.SlashCommandGroup(_alias(), "Commands related to generating TOTPs")

    @auth.command(name="code", description="Generates an OTP with a 2FA Secret")
    async def command(
        self,
        ctx: discord.ApplicationContext,
        secret: discord.Option(str, "The base32 authenticator secret"),
    ):
        if ctx.author.id not in self.bot.admins:
            return await ctx.respond(
                "You do not have permission!", ephemeral=True
            )

        code = await totp(secret.strip())
        if code:
            await ctx.respond(
                embed=discord.Embed(
                    title="Authenticator Code",
                    description=f"```{code}```",
                ),
                view=ButtonTOTP(secret.strip()),
                ephemeral=True,
            )
            return

        await ctx.respond("This secret is invalid.", ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(AuthCode(bot))
