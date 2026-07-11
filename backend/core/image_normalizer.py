from io import BytesIO

from PIL import Image, UnidentifiedImageError
from pillow_heif import register_heif_opener

# Lets Pillow decode Apple formats (HEIC/HEIF) uploaded by iPhones
register_heif_opener()

# Formats every browser can display; anything else gets converted
WEB_SAFE_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}

JPEG_QUALITY = 88


def normalize_to_web_format(file):
    """Convert an uploaded image to JPEG unless it is already web-displayable.

    Returns the original file untouched for web-safe formats and for
    non-image payloads; otherwise returns a BytesIO with a .jpg name.
    """
    data = file.read()
    try:
        img = Image.open(BytesIO(data))
        source_format = img.format
    except (UnidentifiedImageError, TypeError):
        # Not decodable as an image: store as-is, like before
        file.seek(0)
        return file

    if source_format in WEB_SAFE_FORMATS:
        file.seek(0)
        return file

    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    out = BytesIO()
    img.save(out, format="JPEG", quality=JPEG_QUALITY)
    out.seek(0)

    base_name = file.name.rsplit(".", 1)[0] if "." in file.name else file.name
    out.name = f"{base_name}.jpg"
    return out
