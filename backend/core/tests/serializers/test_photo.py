import unittest
from unittest.mock import MagicMock, patch
from core import media_signing
from core.serializers.album import media_cache_buster
from core.serializers.photo import PhotoSerializer
from core.models.photo import Photo
from core.models.album import Album
from rest_framework.exceptions import ValidationError

TEST_PHOTO_ID = 101
TEST_IMAGE_URL = "https://example.com/image.jpg"
TEST_CAPTION = "Souvenir"
TEST_LOCATION = "Paris"
TEST_VALID_DATA = {
    "image_url": TEST_IMAGE_URL,
    "caption": TEST_CAPTION,
    "location": TEST_LOCATION,
}


class TestPhotoSerializer(unittest.TestCase):

    def setUp(self):
        self.mock_request = MagicMock()
        self.mock_user = MagicMock()
        self.mock_request.user = self.mock_user
        self.mock_album = MagicMock(spec=Album)

        self.context = {"request": self.mock_request, "album": self.mock_album}
        self.serializer = PhotoSerializer(context=self.context)

    @patch("core.serializers.album.Photo")
    def test_givenPhotoInstance_whenSerialize_thenShouldContainExpectedFields(
        self, mock_album_photo
    ):
        mock_photo = MagicMock(spec=Photo)
        mock_photo.id = TEST_PHOTO_ID
        mock_photo.image_url = TEST_IMAGE_URL
        mock_photo.caption = TEST_CAPTION
        mock_photo.location = TEST_LOCATION
        mock_photo.created_at = "2023-01-01"
        mock_photo.updated_at = "2023-01-02"
        mock_photo.album = self.mock_album
        self.mock_album.cover_image = None

        mock_album_photo.objects.filter.return_value.count.return_value = 0

        serializer = PhotoSerializer(instance=mock_photo)
        data = serializer.data

        expected_url = (
            f"/api/media/photos/{TEST_PHOTO_ID}/{media_signing.sign(TEST_IMAGE_URL)}/"
            f"?v={media_cache_buster(TEST_IMAGE_URL)}"
        )
        self.assertEqual(data["image_url"], expected_url)

    def test_givenUnauthenticatedUser_whenCreate_thenShouldReturnNone(self):
        self.mock_user.is_authenticated = False

        result = self.serializer.create(TEST_VALID_DATA)

        self.assertIsNone(result)

    def test_givenAuthenticatedUserButNoAlbumInContext_whenCreate_thenShouldRaiseValidationError(
        self,
    ):
        self.mock_user.is_authenticated = True
        context_without_album = {"request": self.mock_request}
        serializer_no_album = PhotoSerializer(context=context_without_album)

        with self.assertRaises(ValidationError):
            serializer_no_album.create(TEST_VALID_DATA)

    @patch("core.serializers.photo.Photo.objects.create")
    def test_givenAuthenticatedUserAndAlbum_whenCreate_thenShouldCreatePhotoLinkedToAlbum(
        self, mock_create
    ):
        self.mock_user.is_authenticated = True

        self.serializer.create(TEST_VALID_DATA)

        mock_create.assert_called_once_with(album=self.mock_album, **TEST_VALID_DATA)

    @patch("core.serializers.photo.Photo.objects.create")
    def test_givenAlbumInValidatedData_whenCreate_thenShouldNotPassAlbumTwice(
        self, mock_create
    ):
        # serializer.save(album=...) injects album into validated_data:
        # create() must not forward it twice to objects.create()
        self.mock_user.is_authenticated = True
        data_with_album = {**TEST_VALID_DATA, "album": self.mock_album}

        self.serializer.create(data_with_album)

        mock_create.assert_called_once_with(album=self.mock_album, **TEST_VALID_DATA)

    @patch("core.serializers.photo.Photo.objects.create")
    def test_givenAuthenticatedUserAndAlbum_whenCreate_thenShouldReturnCreatedInstance(
        self, mock_create
    ):
        self.mock_user.is_authenticated = True
        mock_instance = MagicMock()
        mock_create.return_value = mock_instance

        result = self.serializer.create(TEST_VALID_DATA)

        self.assertEqual(result, mock_instance)


if __name__ == "__main__":
    unittest.main()
