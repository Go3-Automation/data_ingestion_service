from datetime import datetime
import unittest
from unittest.mock import patch, MagicMock
from data_ingestion_service.upload import DIIPUploader
from botocore.response import StreamingBody
import io


class TestDIIPUploader(unittest.TestCase):

    @patch('data_ingestion_service.upload.requests')
    def test_initialize_upload(self, mock_requests):
        """Test that the upload session is initialized correctly."""
        mock_requests.request.return_value.status_code = 200
        mock_requests.request.return_value.json.return_value = {'dataPackageId': '12345'}

        uploader = DIIPUploader(base_url='https://example.com', api_key='test-api-key')
        data_package_id = uploader._initialize_upload()

        self.assertEqual(data_package_id, '12345')
        mock_requests.request.assert_called_once_with(
            'POST',
            'https://example.com/upload/init',
            headers={'x-api-key': 'test-api-key'},
            json=None
        )

    @patch('data_ingestion_service.upload.requests')
    def test_complete_upload(self, mock_requests):
        """Test that the upload session is completed correctly."""
        mock_requests.request.return_value.status_code = 200

        uploader = DIIPUploader(base_url='https://example.com', api_key='test-api-key')
        uploader.data_package_id = '12345'
        uploader._complete_upload()

        mock_requests.request.assert_called_once_with(
            'POST',
            'https://example.com/upload/12345/complete',
            headers={'x-api-key': 'test-api-key'},
            json=None
        )

    @patch('data_ingestion_service.upload.requests')
    def test_upload_file_local(self, mock_requests):
        """Test uploading a local file."""
        mock_requests.post.return_value.status_code = 204

        with DIIPUploader(base_url='https://example.com', api_key='test-api-key') as uploader:
            uploader._entity_url_cache['test_entity'] = (
                {'url': 'https://s3.amazonaws.com', 'fields': {}},
                datetime.now()
            )
            uploader.upload_file(entity_name='test_entity', file='test_file.txt')

        mock_requests.post.assert_called_once()
        self.assertEqual(mock_requests.post.call_args[1]['files']['file'][0], 'test_file.txt')

    @patch('data_ingestion_service.upload.requests')
    def test_upload_file_in_memory(self, mock_requests):
        """Test uploading an in-memory file."""
        mock_requests.post.return_value.status_code = 204
        mock_file = io.BytesIO(b'test content')

        with DIIPUploader(base_url='https://example.com', api_key='test-api-key') as uploader:
            uploader._entity_url_cache['test_entity'] = (
                {'url': 'https://s3.amazonaws.com', 'fields': {}},
                datetime.now()
            )
            #assert typep e(mock_file) == io.BytesIO
            assert isinstance(mock_file, io.BytesIO)
            uploader.upload_file(entity_name='test_entity', file=mock_file, file_name='test_file.txt')

        mock_requests.post.assert_called_once()
        self.assertEqual(mock_requests.post.call_args[1]['files']['file'][0], 'test_file.txt')

    @patch('data_ingestion_service.upload.requests')
    def test_upload_file_streaming_body(self, mock_requests):
        """Test uploading a file from a StreamingBody."""
        mock_requests.post.return_value.status_code = 204
        streaming_body_mock = MagicMock(spec=StreamingBody)
        streaming_body_mock.read.return_value = b'test content'

        with DIIPUploader(base_url='https://example.com', api_key='test-api-key') as uploader:
            uploader._entity_url_cache['test_entity'] = (
                {'url': 'https://s3.amazonaws.com', 'fields': {}},
                datetime.now()
            )
            uploader.upload_file(entity_name='test_entity', file=streaming_body_mock, file_name='test_file.txt')

        mock_requests.post.assert_called_once()
        self.assertEqual(mock_requests.post.call_args[1]['files']['file'][0], 'test_file.txt')

    @patch('data_ingestion_service.upload.requests')
    def test_upload_file_failure(self, mock_requests):
        """Test handling of a failed upload."""
        mock_requests.post.return_value.status_code = 400
        mock_requests.post.return_value.text = 'Bad Request'

        with DIIPUploader(base_url='https://example.com', api_key='test-api-key') as uploader:
            uploader._entity_url_cache['test_entity'] = (
                {'url': 'https://s3.amazonaws.com', 'fields': {}},
                datetime.now()
            )
            with self.assertRaises(Exception) as context:
                uploader.upload_file(entity_name='test_entity', file='test_file.txt')

        self.assertIn('Failed to upload file test_file.txt', str(context.exception))

    @patch('data_ingestion_service.upload.requests')
    def test_context_manager(self, mock_requests):
        """Test that the context manager initializes and completes the upload session."""
        mock_requests.request.return_value.status_code = 200
        mock_requests.request.return_value.json.return_value = {'dataPackageId': '12345'}

        with DIIPUploader(base_url='https://example.com', api_key='test-api-key') as uploader:
            self.assertEqual(uploader.data_package_id, '12345')

        mock_requests.request.assert_any_call(
            'POST',
            'https://example.com/upload/init',
            headers={'x-api-key': 'test-api-key'},
            json=None
        )
        mock_requests.request.assert_any_call(
            'POST',
            'https://example.com/upload/12345/complete',
            headers={'x-api-key': 'test-api-key'},
            json=None
        )


if __name__ == '__main__':
    unittest.main()

