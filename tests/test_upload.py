import unittest
from data_ingestion_service.upload import diip_uploader
from unittest.mock import patch, MagicMock

class TestDiipUploader(unittest.TestCase):

    @patch('data_ingestion_service.upload.requests')
    def test_upload_file_local(self, mock_requests):
        mock_requests.post.return_value.status_code = 204
        mock_requests.post.return_value.text = ''
        
        with diip_uploader(base_url='https://ingest-api.uat.diip.go3.tv', api_key='your-api-key') as uploader:
            uploader.upload_file(entity_name='test_entity', file='test_file.txt')

        mock_requests.post.assert_called_once()

    @patch('data_ingestion_service.upload.requests')
    def test_upload_file_in_memory(self, mock_requests):
        mock_requests.post.return_value.status_code = 204
        mock_requests.post.return_value.text = ''
        
        with diip_uploader(base_url='https://ingest-api.uat.diip.go3.tv', api_key='your-api-key') as uploader:
            uploader.upload_file(entity_name='test_entity', file=MagicMock(), file_name='test_file.txt')

        mock_requests.post.assert_called_once()

    @patch('data_ingestion_service.upload.requests')
    def test_upload_file_streaming_body(self, mock_requests):
        mock_requests.post.return_value.status_code = 204
        mock_requests.post.return_value.text = ''
        
        streaming_body_mock = MagicMock()
        streaming_body_mock.read.return_value = b'test content'
        
        with diip_uploader(base_url='https://ingest-api.uat.diip.go3.tv', api_key='your-api-key') as uploader:
            uploader.upload_file(entity_name='test_entity', file=streaming_body_mock, file_name='test_file.txt')

        mock_requests.post.assert_called_once()

    @patch('data_ingestion_service.upload.requests')
    def test_upload_file_failure(self, mock_requests):
        mock_requests.post.return_value.status_code = 400
        mock_requests.post.return_value.text = 'Bad Request'
        
        with diip_uploader(base_url='https://ingest-api.uat.diip.go3.tv', api_key='your-api-key') as uploader:
            with self.assertRaises(Exception) as context:
                uploader.upload_file(entity_name='test_entity', file='test_file.txt')

        self.assertTrue('Failed to upload file test_file.txt' in str(context.exception))

if __name__ == '__main__':
    unittest.main()