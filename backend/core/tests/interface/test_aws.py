import unittest
from unittest.mock import MagicMock, patch
from core.interface.aws import AwsPhotoSaver
from core.exceptions.exceptions import CloudUploadError, ResourceNotFound
from botocore.exceptions import ClientError

TEST_AWS_BUCKET_NAME = "testing_bucket_name"
TEST_AWS_REGION = "us-east-1"
TEST_FILE_NAME = "photo.jpg"
TEST_GENERATED_UUID = "1234-5678"
TEST_ALBUM_FOLDER_ID = "album_1"
TEST_S3_KEY = f"{TEST_GENERATED_UUID}_{TEST_FILE_NAME}"
TEST_S3_KEY_FOLDER = f"{TEST_ALBUM_FOLDER_ID}/{TEST_GENERATED_UUID}_{TEST_FILE_NAME}"
TEST_DEBUG_KEY = f"debug_{TEST_GENERATED_UUID}_{TEST_FILE_NAME}"
TEST_EXPECTED_URL = (
    f"https://{TEST_AWS_BUCKET_NAME}.s3.{TEST_AWS_REGION}.amazonaws.com/{TEST_S3_KEY}"
)
TEST_EXPECTED_URL_FOLDER = f"https://{TEST_AWS_BUCKET_NAME}.s3.{TEST_AWS_REGION}.amazonaws.com/{TEST_S3_KEY_FOLDER}"


class TestAwsPhotoSaver(unittest.TestCase):

    def setUp(self):
        self.mock_file = MagicMock()
        self.mock_file.name = TEST_FILE_NAME
        self.aws_saver = AwsPhotoSaver()

    @patch("core.interface.aws.boto3")
    @patch("core.interface.aws.uuid4")
    @patch("core.interface.aws.AWS_BUCKET_NAME", TEST_AWS_BUCKET_NAME)
    @patch("core.interface.aws.DEBUG", False)
    def test_givenAValidFile_whenSave_thenShouldUploadToS3(self, mock_uuid, mock_boto3):
        mock_uuid.return_value = TEST_GENERATED_UUID
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        self.aws_saver.save(self.mock_file)

        mock_s3_client.upload_fileobj.assert_called_once()

    @patch("core.interface.aws.boto3")
    @patch("core.interface.aws.uuid4")
    @patch("core.interface.aws.AWS_BUCKET_NAME", TEST_AWS_BUCKET_NAME)
    @patch("core.interface.aws.AWS_REGION", TEST_AWS_REGION)
    @patch("core.interface.aws.DEBUG", False)
    def test_givenAValidFile_whenSave_thenShouldReturnCorrectUrl(
        self, mock_uuid, mock_boto3
    ):
        mock_uuid.return_value = TEST_GENERATED_UUID
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        result = self.aws_saver.save(self.mock_file)

        self.assertEqual(result, TEST_EXPECTED_URL)

    @patch("core.interface.aws.boto3")
    @patch("core.interface.aws.uuid4")
    @patch("core.interface.aws.AWS_BUCKET_NAME", TEST_AWS_BUCKET_NAME)
    @patch("core.interface.aws.DEBUG", False)
    def test_givenAValidFileAndFolder_whenSaveWithinFolder_thenShouldUploadToS3WithPrefix(
        self, mock_uuid, mock_boto3
    ):
        mock_uuid.return_value = TEST_GENERATED_UUID
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        self.aws_saver.save_within_folder(self.mock_file, TEST_ALBUM_FOLDER_ID)

        args, _ = mock_s3_client.upload_fileobj.call_args
        self.assertEqual(args[2], TEST_S3_KEY_FOLDER)

    @patch("core.interface.aws.boto3")
    @patch("core.interface.aws.uuid4")
    @patch("core.interface.aws.AWS_BUCKET_NAME", TEST_AWS_BUCKET_NAME)
    @patch("core.interface.aws.AWS_REGION", TEST_AWS_REGION)
    @patch("core.interface.aws.DEBUG", False)
    def test_givenAValidFileAndFolder_whenSaveWithinFolder_thenShouldReturnCorrectUrlWithPrefix(
        self, mock_uuid, mock_boto3
    ):
        mock_uuid.return_value = TEST_GENERATED_UUID
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        result = self.aws_saver.save_within_folder(self.mock_file, TEST_ALBUM_FOLDER_ID)

        self.assertEqual(result, TEST_EXPECTED_URL_FOLDER)

    @patch("core.interface.aws.boto3")
    @patch("core.interface.aws.uuid4")
    @patch("core.interface.aws.DEBUG", True)
    def test_givenDebugModeEnabled_whenSave_thenShouldUploadWithDebugPrefix(
        self, mock_uuid, mock_boto3
    ):
        mock_uuid.return_value = TEST_GENERATED_UUID
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        self.aws_saver.save(self.mock_file)

        args, _ = mock_s3_client.upload_fileobj.call_args
        self.assertEqual(args[2], TEST_DEBUG_KEY)

    @patch("core.interface.aws.boto3")
    @patch("core.interface.aws.uuid4")
    @patch("core.interface.aws.DEBUG", False)
    def test_givenS3UploadFails_whenSave_thenShouldRaiseCloudUploadError(
        self, mock_uuid, mock_boto3
    ):
        mock_uuid.return_value = TEST_GENERATED_UUID
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client
        mock_s3_client.upload_fileobj.side_effect = ClientError(
            {"Error": {"Code": "500"}}, "upload_fileobj"
        )

        with self.assertRaises(CloudUploadError):
            self.aws_saver.save(self.mock_file)

    @patch("core.interface.aws.boto3")
    @patch("core.interface.aws.AWS_BUCKET_NAME", TEST_AWS_BUCKET_NAME)
    def test_givenAValidUrl_whenDelete_thenShouldCallDeleteObject(self, mock_boto3):
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        self.aws_saver.delete(TEST_EXPECTED_URL)

        mock_s3_client.delete_object.assert_called_once()

    @patch("core.interface.aws.boto3")
    @patch("core.interface.aws.AWS_BUCKET_NAME", TEST_AWS_BUCKET_NAME)
    def test_givenAValidUrl_whenDelete_thenShouldDeleteCorrectKey(self, mock_boto3):
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        self.aws_saver.delete(TEST_EXPECTED_URL)

        mock_s3_client.delete_object.assert_called_with(
            Bucket=TEST_AWS_BUCKET_NAME, Key=TEST_S3_KEY
        )

    @patch("core.interface.aws.boto3")
    def test_givenNoneUrl_whenDelete_thenShouldNotCallDeleteObject(self, mock_boto3):
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        self.aws_saver.delete(None)

        mock_s3_client.delete_object.assert_not_called()

    @patch("core.interface.aws.boto3")
    def test_givenNoneUrl_whenDelete_thenShouldReturnTrue(self, mock_boto3):
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client

        result = self.aws_saver.delete(None)

        self.assertTrue(result)

    @patch("core.interface.aws.boto3")
    @patch("core.interface.aws.AWS_BUCKET_NAME", TEST_AWS_BUCKET_NAME)
    def test_givenS3DeletionFails_whenDelete_thenShouldRaiseCloudUploadError(
        self, mock_boto3
    ):
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client
        mock_s3_client.delete_object.side_effect = Exception("Error")

        with self.assertRaises(CloudUploadError):
            self.aws_saver.delete(TEST_EXPECTED_URL)


if __name__ == "__main__":
    unittest.main()


class TestAwsPhotoSaverFetch(unittest.TestCase):

    def setUp(self):
        self.aws_saver = AwsPhotoSaver()

    @patch("core.interface.aws.boto3")
    @patch("core.interface.aws.AWS_BUCKET_NAME", TEST_AWS_BUCKET_NAME)
    @patch("core.interface.aws.AWS_REGION", TEST_AWS_REGION)
    def test_givenExistingKey_whenFetch_thenShouldReturnBytesAndContentType(
        self, mock_boto3
    ):
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client
        mock_body = MagicMock()
        mock_body.read.return_value = b"image bytes"
        mock_s3_client.get_object.return_value = {
            "Body": mock_body,
            "ContentType": "image/jpeg",
        }

        data, content_type = self.aws_saver.fetch(TEST_EXPECTED_URL)

        self.assertEqual(data, b"image bytes")
        self.assertEqual(content_type, "image/jpeg")
        mock_s3_client.get_object.assert_called_once_with(
            Bucket=TEST_AWS_BUCKET_NAME, Key=TEST_S3_KEY
        )

    @patch("core.interface.aws.boto3")
    @patch("core.interface.aws.AWS_BUCKET_NAME", TEST_AWS_BUCKET_NAME)
    @patch("core.interface.aws.AWS_REGION", TEST_AWS_REGION)
    def test_givenMissingKey_whenFetch_thenShouldRaiseResourceNotFound(
        self, mock_boto3
    ):
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client
        mock_s3_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "does not exist"}},
            "GetObject",
        )

        with self.assertRaises(ResourceNotFound):
            self.aws_saver.fetch(TEST_EXPECTED_URL)

    @patch("core.interface.aws.boto3")
    @patch("core.interface.aws.AWS_BUCKET_NAME", TEST_AWS_BUCKET_NAME)
    @patch("core.interface.aws.AWS_REGION", TEST_AWS_REGION)
    def test_givenOtherS3Error_whenFetch_thenShouldRaiseCloudUploadError(
        self, mock_boto3
    ):
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client
        mock_s3_client.get_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}},
            "GetObject",
        )

        with self.assertRaises(CloudUploadError):
            self.aws_saver.fetch(TEST_EXPECTED_URL)
