"""Secure accounts via recovery code / password-secret with bulk support."""

import json
import logging

import discord
from discord.ext import commands

from ui.modals.recovery_code import recoveryCodeModal
from ui.modals.recovery_code_bulk import BulkRecoveryCodeModal
from ui.modals.recovery_secret import recoveryAuthModal
from ui.modals.recovery_secret_bulk import BulkAuthRecoveryModal

log = logging.getLogger("bot")


def _alias() -> str:
    with open("config/bot.json") as f:
        return json.load(f)["enabled_commands"]["aliases"]["secure"]


class Dropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Recovery Code",
                description="Uses email + recovery code",
                value="rcvcode",
            ),
            discord.SelectOption(
                label="Recovery Code Bulk",
                description="Uses email + recovery code",
                value="bulk_rcvcode",
            ),
            discord.SelectOption(
                label="Password + Secret",
                description="Uses auth secret and password",
                value="pwdsecret",
            ),
            discord.SelectOption(
                label="Password + Secret Bulk",
                description="Bulk option for password + secret",
                value="bulk_pwdsecret",
            ),
        ]
        super().__init__(
            placeholder="Select Securing Method",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        match selected:
            case "rcvcode":
                modal = recoveryCodeModal()
            case "bulk_rcvcode":
                modal = BulkRecoveryCodeModal()
            case "pwdsecret":
                modal = recoveryAuthModal()
            case "bulk_pwdsecret":
                modal = BulkAuthRecoveryModal()
            case _:
                return

        await interaction.response.send_modal(modal)


class Secure(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @discord.slash_command(name=_alias(), description="Automatically secures your account")
    async def secure(self, ctx: discord.ApplicationContext):
        if ctx.author.id not in self.bot.admins:
            await ctx.respond(
                "You do not have permission to execute this command!", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Select Securing Method",
            description=(
                "Choose how you want to authenticate:\n\n"
                "**Recovery Code**\n"
                "Use your email and recovery code\n\n"
                "**Recovery Code Bulk**\n"
                "Secures multiple accounts via recovery code\n\n"
                "**Password + Secret (Needs 2FA)**\n"
                "Use your email, password and authenticator secret\n\n"
                "**Password + Secret Bulk**\n"
                "Secure multiple accounts via pwd and secret"
            ),
        )

        view = discord.ui.View()
        view.add_item(Dropdown())

        await ctx.respond(embed=embed, view=view, ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Secure(bot))
