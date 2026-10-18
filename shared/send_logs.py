"""Log embeds to Discord channels (full + censored)."""

import datetime
import json
import logging

from discord import Client, Embed, Member

log = logging.getLogger("bot")


def censor_mail(email: str) -> str:
    """Mask local-part and first domain label, preserving structure."""
    try:
        user, domain = email.rsplit("@", 1)

        def mask(s: str) -> str:
            if len(s) <= 1:
                return "*"
            if len(s) == 2:
                return s[0] + "*"
            return s[0] + "*" * (len(s) - 2) + s[-1]

        parts = domain.split(".")
        masked_domain = mask(parts[0]) + "." + ".".join(parts[1:])
        return f"{mask(user)}@{masked_domain}"
    except Exception:
        return "***@***"


def build_log_embed(
    description: str,
    color: int,
    thumbnail: str | None = None,
    user: Member | None = None,
    bot: Client | None = None,
) -> Embed:
    embed = Embed(description=description, colour=color)

    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    if user:
        embed.set_author(
            name=f"{user.name} | {user.id}",
            icon_url=user.display_avatar.url,
        )

    bot_name = bot.user.name if bot else "Verify Bot"
    footer_icon = bot.user.display_avatar.url if bot else None
    embed.set_footer(
        text=f"{bot_name} • {datetime.datetime.now().strftime('%d/%m/%Y, %H:%M')}",
        icon_url=footer_icon,
    )

    return embed


async def send_logs(
    bot: Client,
    embed: Embed | None = None,
    view=None,
    content: str | None = None,
    email: str | None = None,
    censored_only: bool = False,
) -> None:
    config = json.load(open("config/config.json", "r"))
    logs_channel_id = config["discord"]["logs_channel"]
    censored_logs_channel_id = config["discord"]["censored_logs_channel"]

    if not censored_only:
        channel = await bot.fetch_channel(logs_channel_id)
        await channel.send(content=content, embed=embed, view=view)

    if censored_logs_channel_id and censored_logs_channel_id != logs_channel_id:
        censored_channel = await bot.fetch_channel(censored_logs_channel_id)

        censored_embed = None
        if embed is not None:
            embed_dict = embed.to_dict()
            if email and "description" in embed_dict:
                embed_dict["description"] = embed_dict["description"].replace(
                    email, censor_mail(email)
                )
            censored_embed = Embed.from_dict(embed_dict)

        await censored_channel.send(content=content, embed=censored_embed, view=view)
