"""TOTP generation from a base32 secret — RFC 6238 HOTP/TOTP."""

import base64
import hashlib
import hmac
import struct
import time


async def totp(secret: str) -> str | None:
    """Generate a 6-digit TOTP code from a base32 secret.

    Returns ``None`` if the secret is invalid base32.
    """
    try:
        secret = secret.upper().replace(" ", "").replace("\n", "").replace("\r", "")

        padding = (8 - len(secret) % 8) % 8
        secret_padded = secret + "=" * padding

        key = base64.b32decode(secret_padded)
        counter = int(time.time()) // 30
        msg = struct.pack(">Q", counter)
        digest = hmac.new(key, msg, hashlib.sha1).digest()

        offset = digest[-1] & 15
        code = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
        return f"{code % 1_000_000:06d}"
    except Exception:
        return None
