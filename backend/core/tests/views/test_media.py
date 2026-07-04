from io import BytesIO
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase
from PIL import Image
from rest_framework import status
from rest_framework.test import APIRequestFactory

from core import media_signing
from core.exceptions.exceptions import CloudUploadError, ResourceNotFound
from core.models import Album, Photo
from core.views.media import MediaPhotoView, MediaAlbumCoverView

TEST_IMAGE_URL = "https://bucket.s3.eu-north-1.amazonaws.com/1/uuid_photo.jpg"
TEST_COVER_URL = "https://bucket.s3.eu-north-1.amazonaws.com/uuid_cover.jpg"


def make_image_bytes(width=2000, height=1500, fmt="JPEG"):
    img = Image.new("RGB", (width, height), color=(120, 30, 60))
    out = BytesIO()
    img.save(out, format=fmt)
    return out.getvalue()


class TestMediaPhotoView(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = APIRequestFactory()
        self.view = MediaPhotoView.as_view()
        self.album = Album.objects.create(title="Album", description="d")
        self.photo = Photo.objects.create(album=self.album, image_url=TEST_IMAGE_URL)
        self.sig = media_signing.sign(TEST_IMAGE_URL)

    def _get(self, path_suffix="", sig=None, photo_id=None):
        sig = sig or self.sig
        photo_id = photo_id or self.photo.id
        request = self.factory.get(f"/media/photos/{photo_id}/{sig}/{path_suffix}")
        return self.view(request, photo_id=photo_id, sig=sig)

    @patch("core.services.media_service.photo_repository.fetch")
    def test_returns_image_with_cache_headers(self, mock_fetch):
        mock_fetch.return_value = (make_image_bytes(), "image/jpeg")

        response = self._get()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response["Cache-Control"], "public, max-age=31536000, immutable"
        )
        mock_fetch.assert_called_once_with(TEST_IMAGE_URL)

    @patch("core.services.media_service.photo_repository.fetch")
    def test_width_param_resizes_to_webp(self, mock_fetch):
        mock_fetch.return_value = (make_image_bytes(2000, 1500), "image/jpeg")

        response = self._get("?w=480")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/webp")
        img = Image.open(BytesIO(response.content))
        self.assertLessEqual(img.width, 480)
        self.assertLessEqual(img.height, 480)

    @patch("core.services.media_service.photo_repository.fetch")
    def test_small_image_passes_through_unmodified(self, mock_fetch):
        raw = make_image_bytes(200, 150)
        mock_fetch.return_value = (raw, "image/jpeg")

        response = self._get()

        self.assertEqual(response.content, raw)
        self.assertEqual(response["Content-Type"], "image/jpeg")

    @patch("core.services.media_service.photo_repository.fetch")
    def test_heic_is_converted_to_webp_even_when_small(self, mock_fetch):
        # Apple HEIC stored with a lying content type must still be converted
        raw = make_image_bytes(200, 150, fmt="HEIF")
        mock_fetch.return_value = (raw, "application/octet-stream")

        response = self._get()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/webp")
        img = Image.open(BytesIO(response.content))
        self.assertEqual(img.format, "WEBP")

    @patch("core.services.media_service.photo_repository.fetch")
    def test_gif_passes_through_unmodified(self, mock_fetch):
        raw = make_image_bytes(2000, 1500, fmt="GIF")
        mock_fetch.return_value = (raw, "image/gif")

        response = self._get("?w=480")

        self.assertEqual(response.content, raw)
        self.assertEqual(response["Content-Type"], "image/gif")

    def test_invalid_width_returns_400(self):
        for bad_width in ["abc", "-1", "0", "9999"]:
            response = self._get(f"?w={bad_width}")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("core.services.media_service.photo_repository.fetch")
    def test_file_missing_on_s3_returns_404(self, mock_fetch):
        mock_fetch.side_effect = ResourceNotFound("Fichier absent de S3")

        response = self._get()

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("core.services.media_service.photo_repository.fetch")
    def test_s3_failure_returns_503(self, mock_fetch):
        mock_fetch.side_effect = CloudUploadError("S3 injoignable")

        response = self._get()

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    def test_unknown_photo_returns_404(self):
        response = self._get(photo_id=9999)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_tampered_signature_returns_403(self):
        response = self._get(sig="0" * 16)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("core.services.media_service.photo_repository.fetch")
    def test_download_param_sets_content_disposition(self, mock_fetch):
        mock_fetch.return_value = (make_image_bytes(200, 150), "image/jpeg")

        response = self._get("?download=1")

        self.assertEqual(response["Content-Disposition"], "attachment")

    @patch("core.services.media_service.photo_repository.fetch")
    def test_second_call_is_served_from_cache(self, mock_fetch):
        mock_fetch.return_value = (make_image_bytes(200, 150), "image/jpeg")

        first = self._get()
        second = self._get()

        self.assertEqual(first.content, second.content)
        mock_fetch.assert_called_once()


class TestMediaAlbumCoverView(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = APIRequestFactory()
        self.view = MediaAlbumCoverView.as_view()
        self.album = Album.objects.create(
            title="Album", description="d", cover_image=TEST_COVER_URL
        )
        self.sig = media_signing.sign(TEST_COVER_URL)

    def _get(self, album_id, sig):
        request = self.factory.get(f"/media/albums/{album_id}/cover/{sig}/")
        return self.view(request, album_id=album_id, sig=sig)

    @patch("core.services.media_service.photo_repository.fetch")
    def test_returns_cover_image(self, mock_fetch):
        mock_fetch.return_value = (make_image_bytes(200, 150), "image/jpeg")

        response = self._get(self.album.id, self.sig)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_fetch.assert_called_once_with(TEST_COVER_URL)

    def test_unknown_album_returns_404(self):
        response = self._get(9999, self.sig)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_album_without_cover_returns_404(self):
        bare_album = Album.objects.create(title="NoCover", description="d")
        response = self._get(bare_album.id, self.sig)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
