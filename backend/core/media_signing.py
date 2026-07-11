import hashlib
import hmac

from django.conf import settings


def sign(file_url: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(), file_url.encode(), hashlib.sha256
    ).hexdigest()[:16]


def verify(file_url: str, signature: str) -> bool:
    return hmac.compare_digest(sign(file_url), signature)
