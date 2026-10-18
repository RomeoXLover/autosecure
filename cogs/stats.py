"""Minecraft stats cog — donut, hypixel, and seller stats."""

import json
import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands

from database.database import DBConnection
from minecraft.get_donut import get_donut_stats, parse_donut_result
from minecraft.get_hypixel import get_hypixel_stats
from shared.simplify import simplify

log = logging.getLogger("bot")


def _alias() -> str:
    with open("config/bot.json") as f:
        return json.load(f)["enabled_commands"]["aliases"]["stats"]


class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    stats = discord.SlashCommandGroup(_alias())

    @stats.command(name="donut", description="Checks your donut stats")
    async def donut(
        self,
        ctx: discord.ApplicationContext,
        username: discord.Option(str, "Minecraft username"),
    ):
        if ctx.author.id not in self.bot.admins:
            await ctx.respond(
                "You do not have permission to execute this command!", ephemeral=True
            )
            return

        await ctx.defer(ephemeral=True)

        donut_stats = await get_donut_stats(username)
        if not donut_stats:
            await ctx.followup.send(
                "Set up your donut API key first!", ephemeral=True
            )
            return

        result = parse_donut_result(donut_stats)
        if not result:
            await ctx.followup.send(
                "That player doesn't have stats!", ephemeral=True
            )
            return

        ms = int(float(result["playtime"])) if result["playtime"] else 0
        days = ms // 86400000
        hours = (ms % 86400000) // 3600000

        embed = discord.Embed(
            title=f"Stats for {username}",
            description=(
                f"**Money**: `${simplify(result['money'])}`\n"
                f"**Shards**: `{simplify(result['shards'])}`\n"
                f"**Player Kills**: `{simplify(result['kills'])}`\n"
                f"**Deaths**: `{simplify(result['deaths'])}`\n"
                f"**Playtime**: `{days}d {hours}h`\n"
                f"**Blocks Placed**: `{simplify(result['placed_blocks'])}`\n"
                f"**Blocks Broken**: `{simplify(result['broken_blocks'])}`\n"
                f"**Mobs Killed**: `{simplify(result['mobs_killed'])}`\n"
                f"**Money Spent**: `${simplify(result['money_spent_on_shop'])}`\n"
                f"**Money Made**: `${simplify(result['money_made_from_sell'])}`"
            ),
            timestamp=datetime.now(timezone.utc),
            color=0xFF9E45,
        )
        embed.set_thumbnail(url=f"https://mc-heads.net/avatar/{username}/60")
        await ctx.followup.send(embed=embed, ephemeral=True)

    @stats.command(name="hypixel", description="Checks your Hypixel stats")
    async def hypixel(
        self,
        ctx: discord.ApplicationContext,
        username: discord.Option(str, "Minecraft username"),
    ):
        if ctx.author.id not in self.bot.admins:
            await ctx.respond(
                "You do not have permission to execute this command!", ephemeral=True
            )
            return

        await ctx.defer(ephemeral=True)

        hypixel_stats = await get_hypixel_stats(username)
        if not hypixel_stats.get("exists"):
            await ctx.followup.send(
                "Make sure you setup your Skytools key first!", ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"{hypixel_stats['hypixel']['rank']} Rank - {username.capitalize()}",
            description=(
                f"**Hypixel Level**: `{hypixel_stats['hypixel']['level']}`\n"
                f"**Gifted Ranks**: `{hypixel_stats['hypixel']['gifted']}`\n"
                f"**Karma**: `{simplify(hypixel_stats['hypixel']['karma'])}`\n"
                "\n"
                f"**SkyBlock Level**: `{hypixel_stats['skyblock']['level']}`\n"
                f"**Networth**: `{simplify(hypixel_stats['skyblock']['networth'])} Coins`\n"
                "\n"
                f"**BW Wins**: `{hypixel_stats['bedwars']['wins']}`\n"
                f"**BW Deaths**: `{hypixel_stats['bedwars']['deaths']}`\n"
                f"**BW Kills**: `{hypixel_stats['bedwars']['kills']}`\n"
                f"**BW Final Kills**: `{hypixel_stats['bedwars']['final_kills']}`\n"
                f"**BW K/D**: `{hypixel_stats['bedwars']['kd']}`\n"
                "\n"
                f"**SW Wins**: `{hypixel_stats['skywars']['sw_wins']}`\n"
                f"**SW Deaths**: `{hypixel_stats['skywars']['sw_deaths']}`\n"
                f"**SW Kills**: `{hypixel_stats['skywars']['sw_kills']}`\n"
                f"**SW K/D**: `{hypixel_stats['skywars']['sw_kd']}`\n"
            ),
            timestamp=datetime.now(timezone.utc),
            color=0xFF9E45,
        ).set_thumbnail(url=f"https://mc-heads.net/avatar/{username}/60")
        await ctx.followup.send(embed=embed, ephemeral=True)

    @stats.command(name="sell", description="View MFA selling stats")
    async def sell_stats(
        self,
        ctx: discord.ApplicationContext,
        user: discord.Option(
            discord.Member,
            "Seller to look up (defaults to you)",
            required=False,
        ) = None,
    ):
        target = user or ctx.author
        await ctx.defer()

        with DBConnection() as db:
            stats = db.autobuy_seller_stats(target.id)

        embed = discord.Embed(
            title=f"Seller stats — {target.display_name}",
            color=0x2B2D31,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="MFA sold", value=f"**{stats['mfa_sold']}**", inline=True)
        embed.add_field(
            name="Total paid", value=f"**${stats['total_paid_usd']:.2f}**", inline=True
        )
        embed.add_field(
            name="Failed submits", value=f"**{stats['mfa_failed']}**", inline=True
        )
        embed.add_field(
            name="Balance",
            value=(
                f"Available: **${stats['available_usd']:.2f}**\n"
                f"Pending: **${stats['pending_usd']:.2f}**\n"
                f"Withdrawn: **${stats['withdrawn_usd']:.2f}**"
            ),
            inline=False,
        )
        embed.set_footer(text=f"User ID {target.id}")
        await ctx.followup.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Stats(bot))
