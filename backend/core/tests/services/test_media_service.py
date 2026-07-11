from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from core.services.media_service import MediaService
from core.tests.views.test_media import make_image_bytes

TEST_IMAGE_URL = "https://bucket.s3.eu-north-1.amazonaws.com/1/uuid_photo.jpg"


class TestMediaService(TestCase):
    def setUp(self):
        cache.clear()

    def test_cache_key_includes_width(self):
        key_orig = MediaService._cache_key(TEST_IMAGE_URL, None)
        key_480 = MediaService._cache_key(TEST_IMAGE_URL, 480)

        self.assertNotEqual(key_orig, key_480)
        self.assertTrue(key_orig.endswith(":worig"))
        self.assertTrue(key_480.endswith(":w480"))

    def test_width_snaps_to_allowed_values(self):
        self.assertEqual(MediaService._snap_width(100), 240)
        self.assertEqual(MediaService._snap_width(480), 480)
        self.assertEqual(MediaService._snap_width(500), 960)
        self.assertIsNone(MediaService._snap_width(1920))
        self.assertIsNone(MediaService._snap_width(4000))
        self.assertIsNone(MediaService._snap_width(None))

    @override_settings(MEDIA_CACHE_MAX_BYTES=10)
    @patch("core.services.media_service.photo_repository.fetch")
    def test_oversized_payload_is_not_cached(self, mock_fetch):
        mock_fetch.return_value = (make_image_bytes(200, 150), "image/jpeg")

        MediaService.get_image(TEST_IMAGE_URL)
        MediaService.get_image(TEST_IMAGE_URL)

        self.assertEqual(mock_fetch.call_count, 2)

    @patch("core.services.media_service.photo_repository.fetch")
    def test_large_original_is_recompressed_to_webp(self, mock_fetch):
        with override_settings(MEDIA_RECOMPRESS_BYTES=100):
            mock_fetch.return_value = (make_image_bytes(1000, 800), "image/jpeg")

            data, content_type = MediaService.get_image(TEST_IMAGE_URL)

        self.assertEqual(content_type, "image/webp")

    @patch("core.services.media_service.photo_repository.fetch")
    def test_non_image_content_passes_through(self, mock_fetch):
        raw = b"%PDF-1.4 not an image"
        mock_fetch.return_value = (raw, "application/pdf")

        data, content_type = MediaService.get_image(TEST_IMAGE_URL, 480)

        self.assertEqual(data, raw)
        self.assertEqual(content_type, "application/pdf")
