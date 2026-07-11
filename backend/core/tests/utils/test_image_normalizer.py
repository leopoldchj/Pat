from io import BytesIO

from django.test import TestCase
from PIL import Image

from core.image_normalizer import normalize_to_web_format


def make_upload(fmt="JPEG", name="photo.jpg", width=200, height=150, mode="RGB"):
    img = Image.new(mode, (width, height), color=(120, 30, 60) if mode == "RGB" else None)
    out = BytesIO()
    img.save(out, format=fmt)
    out.seek(0)
    out.name = name
    return out


class TestNormalizeToWebFormat(TestCase):
    def test_jpeg_passes_through_untouched(self):
        upload = make_upload(fmt="JPEG", name="photo.jpg")

        result = normalize_to_web_format(upload)

        self.assertIs(result, upload)
        self.assertEqual(result.tell(), 0)

    def test_webp_passes_through_untouched(self):
        upload = make_upload(fmt="WEBP", name="photo.webp")

        result = normalize_to_web_format(upload)

        self.assertIs(result, upload)

    def test_heic_is_converted_to_jpeg(self):
        upload = make_upload(fmt="HEIF", name="IMG_1234.heic")

        result = normalize_to_web_format(upload)

        self.assertIsNot(result, upload)
        self.assertEqual(result.name, "IMG_1234.jpg")
        img = Image.open(result)
        self.assertEqual(img.format, "JPEG")

    def test_transparent_image_is_flattened_on_white(self):
        upload = make_upload(fmt="HEIF", name="logo.heic", mode="RGBA")

        result = normalize_to_web_format(upload)

        img = Image.open(result)
        self.assertEqual(img.format, "JPEG")
        self.assertEqual(img.mode, "RGB")

    def test_non_image_passes_through_untouched(self):
        upload = BytesIO(b"not an image at all")
        upload.name = "document.pdf"

        result = normalize_to_web_format(upload)

        self.assertIs(result, upload)
        self.assertEqual(result.tell(), 0)
