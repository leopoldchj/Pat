import io
from unittest.mock import MagicMock, patch
from django.test import TestCase
from django.contrib.auth.models import User
from core.models.album import Album
from core.models.photo import Photo
from core.models.message import Message
from core.interface.aws import AwsPhotoSaver
from core.exceptions.exceptions import CloudUploadError, ResourceNotFound
from botocore.exceptions import ClientError


class TestDatabaseComponentsIntegration(TestCase):
    """Integration test suite ensuring database component connectivity and lifecycle."""

    def setUp(self):
        # Arrange
        self.user = User.objects.create_user(username="test_contributor", password="secure_password")
        self.album = Album.objects.create(
            title="Summer Trip",
            description="Photos from the integration test expedition",
            cover_image="https://test-bucket.s3.us-east-1.amazonaws.com/cover.jpg"
        )

    def test_givenValidAlbum_whenCreatingRelatedPhotos_thenDatabaseShouldPersistRelationship(self):
        # Arrange
        photo_url_1 = "https://test-bucket.s3.us-east-1.amazonaws.com/photo1.jpg"
        photo_url_2 = "https://test-bucket.s3.us-east-1.amazonaws.com/photo2.jpg"

        # Act
        photo_1 = Photo.objects.create(album=self.album, image_url=photo_url_1, caption="Beach Sunrise")
        photo_2 = Photo.objects.create(album=self.album, image_url=photo_url_2, caption="Sunset Walk")

        # Assert
        persisted_album = Album.objects.get(id=self.album.id)
        self.assertEqual(persisted_album.photos.count(), 2)
        self.assertIn(photo_1, persisted_album.photos.all())
        self.assertIn(photo_2, persisted_album.photos.all())

    def test_givenUserAndMessage_whenSaved_thenDatabaseShouldPersistRecordAndTimestamp(self):
        # Arrange
        message_content = "Hello from integration test!"

        # Act
        message = Message.objects.create(
            user=self.user,
            content=message_content
        )

        # Assert
        retrieved_message = Message.objects.get(id=message.id)
        self.assertEqual(retrieved_message.user, self.user)
        self.assertEqual(retrieved_message.content, message_content)
        self.assertIsNotNone(retrieved_message.created_at)

    def test_givenAlbumWithPhotos_whenAlbumDeleted_thenCascadeShouldRemovePhotos(self):
        # Arrange
        Photo.objects.create(album=self.album, image_url="https://test-bucket.s3.us-east-1.amazonaws.com/temp.jpg")
        photo_count_before = Photo.objects.filter(album=self.album).count()
        self.assertEqual(photo_count_before, 1)

        # Act
        self.album.delete()

        # Assert
        photo_count_after = Photo.objects.filter(album_id=self.album.id).count()
        self.assertEqual(photo_count_after, 0)


class TestAwsComponentsIntegration(TestCase):
    """Integration test suite ensuring AWS storage interface connectivity and error boundary."""

    def setUp(self):
        # Arrange
        self.aws_saver = AwsPhotoSaver()
        self.test_bucket = "pat-integration-bucket"
        self.test_region = "us-east-1"
        self.test_file = io.BytesIO(b"fake image raw byte stream")
        self.test_file.name = "sample_integration.png"

    @patch("core.interface.aws.boto3")
    @patch("core.interface.aws.AWS_BUCKET_NAME", "pat-integration-bucket")
    @patch("core.interface.aws.AWS_REGION", "us-east-1")
    @patch("core.interface.aws.DEBUG", False)
    def test_givenValidBinaryStream_whenSavedWithinFolder_thenShouldCallS3UploadAndReturnSignedUrl(
        self, mock_boto3
    ):
        # Arrange
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3
        folder_name = "album_vacation_2026"

        # Act
        url = self.aws_saver.save_within_folder(self.test_file, folder_name)

        # Assert
        mock_s3.upload_fileobj.assert_called_once()
        self.assertTrue(url.startswith("https://pat-integration-bucket.s3.us-east-1.amazonaws.com/album_vacation_2026/"))

    @patch("core.interface.aws.boto3")
    @patch("core.interface.aws.AWS_BUCKET_NAME", "pat-integration-bucket")
    @patch("core.interface.aws.AWS_REGION", "us-east-1")
    def test_givenMissingS3Resource_whenFetched_thenShouldRaiseDomainResourceNotFound(
        self, mock_boto3
    ):
        # Arrange
        mock_s3 = MagicMock()
        mock_boto3.client.return_value = mock_s3
        mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Key not found"}},
            "GetObject"
        )
        non_existent_url = "https://pat-integration-bucket.s3.us-east-1.amazonaws.com/non_existent.png"

        # Act & Assert
        with self.assertRaises(ResourceNotFound):
            self.aws_saver.fetch(non_existent_url)
