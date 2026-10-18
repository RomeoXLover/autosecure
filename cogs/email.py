"""Email management cog — list, inbox, and create security emails."""

import json
import logging
import uuid

import discord
from discord.ext import commands

from database.database import DBConnection
from ui.buttons.mail_inbox import get_inbox

log = logging.getLogger("bot")


def _alias() -> str:
    with open("config/bot.json") as f:
        return json.load(f)["enabled_commands"]["aliases"]["email"]


class MailListView(discord.ui.View):
    size = 10

    def __init__(self, emails: list, page: int = 0):
        super().__init__(timeout=120)
        self.emails = emails
        self.page = page
        self.total_pages = max(1, (len(emails) + self.size - 1) // self.size)
        self._build_items()

    def _build_items(self):
        prev_btn = discord.ui.Button(
            label="◀",
            style=discord.ButtonStyle.secondary,
            disabled=(self.page == 0),
            row=0,
        )
        prev_btn.callback = self._previous
        self.add_item(prev_btn)

        self.add_item(
            discord.ui.Button(
                label=f"{self.page + 1} / {self.total_pages}",
                style=discord.ButtonStyle.primary,
                disabled=True,
                row=0,
            )
        )

        next_btn = discord.ui.Button(
            label="▶",
            style=discord.ButtonStyle.secondary,
            disabled=(self.page >= self.total_pages - 1),
            row=0,
        )
        next_btn.callback = self._next
        self.add_item(next_btn)

    def build_embed(self) -> discord.Embed:
        start = self.page * self.size
        chunk = self.emails[start : start + self.size]
        lines = "\n".join(
            f"`{start + i + 1}.` {e[0]}" for i, e in enumerate(chunk)
        )
        return discord.Embed(
            title="Security Emails",
            description=f"**{len(self.emails)}** email(s) stored:\n\n{lines}",
            color=0x3B89FF,
        ).set_footer(
            text="These emails are automatically deleted after 7 days"
        )

    async def _previous(self, interaction: discord.Interaction):
        view = MailListView(self.emails, self.page - 1)
        await interaction.response.edit_message(
            embed=view.build_embed(), view=view
        )

    async def _next(self, interaction: discord.Interaction):
        view = MailListView(self.emails, self.page + 1)
        await interaction.response.edit_message(
            embed=view.build_embed(), view=view
        )


class Email(commands.Cog):
    mail = discord.SlashCommandGroup(_alias(), "Commands related email features")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @mail.command(name="new", description="Register a new email address (Needs domain)")
    async def create_mail(
        self,
        ctx: discord.ApplicationContext,
        alias: discord.Option(str, "Alias for the email (e.g. 'recover')"),
    ):
        if ctx.author.id not in self.bot.admins:
            await ctx.respond(
                "You do not have permission to execute this command!", ephemeral=True
            )
            return

        await ctx.response.defer(ephemeral=True)

        password = uuid.uuid4().hex[:12]
        if "@" in alias:
            alias = alias.split("@")[0]

        with open("config/config.json", "r") as f:
            config = json.load(f)
        email = f"{alias}@{config['domain']}"

        with DBConnection() as database:
            existing = database.get_security_emails()
            if email in [e[0] for e in existing]:
                await ctx.respond(
                    embed=discord.Embed(
                        description=f"`{email}` has already been created",
                        color=0xFA4343,
                    ),
                    ephemeral=True,
                )
                return
            database.add_security_email(email, password)

        await ctx.respond(
            embed=discord.Embed(
                title="Email Created",
                description=f"`{email}` has been added!",
                color=0x57F287,
            ),
            ephemeral=True,
        )

    @mail.command(name="inbox", description="Shows the inbox of your email")
    async def email_inbox(
        self,
        ctx: discord.ApplicationContext,
        email: discord.Option(str, "The security email to check"),
    ):
        if ctx.author.id not in self.bot.admins:
            await ctx.respond(
                "You do not have permission to execute this command!", ephemeral=True
            )
            return

        await ctx.response.defer(ephemeral=True)
        inbox = await get_inbox(email)

        if not inbox:
            await ctx.respond(
                embed=discord.Embed(
                    description="This email has not been found",
                    color=0xFA4343,
                ),
                ephemeral=True,
            )
            return

        if len(inbox) == 0:
            await ctx.respond(
                embed=discord.Embed(
                    description="No emails found in inbox.",
                    color=0xFA4343,
                ),
                ephemeral=True,
            )
            return

        await ctx.respond(embed=inbox["embed"], view=inbox["view"], ephemeral=True)

    @mail.command(name="list", description="Lists all security emails")
    async def list_mails(self, ctx: discord.ApplicationContext):
        if ctx.author.id not in self.bot.admins:
            await ctx.respond(
                "You do not have permission to execute this command!", ephemeral=True
            )
            return

        await ctx.response.defer(ephemeral=True)
        with DBConnection() as database:
            emails = list(database.get_security_emails())

        if not emails:
            await ctx.respond(
                embed=discord.Embed(
                    title="No Emails Found",
                    description="You don't have any emails stored",
                    color=0xFA4343,
                ),
                ephemeral=True,
            )
            return

        view = MailListView(emails)
        await ctx.respond(embed=view.build_embed(), view=view, ephemeral=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Email(bot))
