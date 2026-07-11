import hashlib
from io import BytesIO

from django.conf import settings
from django.core.cache import cache
from PIL import Image, UnidentifiedImageError

from core.dependencies import photo_repository
from core.image_normalizer import WEB_SAFE_FORMATS


class MediaService:

    @staticmethod
    def _snap_width(width):
        if width is None:
            return None
        allowed = settings.MEDIA_ALLOWED_WIDTHS
        if width >= max(allowed):
            return None  # full size already capped at MEDIA_MAX_DIMENSION
        return min(w for w in allowed if w >= width)

    @staticmethod
    def _cache_key(file_url: str, width) -> str:
        digest = hashlib.sha256(file_url.encode()).hexdigest()[:32]
        return f"media:{digest}:w{width or 'orig'}"

    @classmethod
    def get_image(cls, file_url: str, width=None) -> tuple[bytes, str]:
        width = cls._snap_width(width)
        cache_key = cls._cache_key(file_url, width)

        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        raw, content_type = photo_repository.fetch(file_url)
        data, content_type = cls._optimize(raw, content_type, width)

        if len(data) <= settings.MEDIA_CACHE_MAX_BYTES:
            cache.set(cache_key, (data, content_type))

        return data, content_type

    @staticmethod
    def _optimize(raw: bytes, content_type: str, width) -> tuple[bytes, str]:
        # Sniff the real format from the bytes: the S3 content type can lie
        # (e.g. Apple HEIC files stored with a wrong name/type)
        try:
            img = Image.open(BytesIO(raw))
            source_format = img.format
        except UnidentifiedImageError:
            return raw, content_type

        # GIFs would lose animation
        if source_format == "GIF":
            return raw, "image/gif"

        needs_convert = source_format not in WEB_SAFE_FORMATS
        needs_recompress = len(raw) > settings.MEDIA_RECOMPRESS_BYTES
        target = width or settings.MEDIA_MAX_DIMENSION
        needs_resize = img.width > target or img.height > target

        if not needs_convert and not needs_recompress and not needs_resize:
            return raw, Image.MIME.get(source_format, content_type)

        if needs_resize:
            img.thumbnail((target, target), Image.LANCZOS)

        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        out = BytesIO()
        img.save(out, format="WEBP", quality=settings.MEDIA_WEBP_QUALITY)
        return out.getvalue(), "image/webp"
