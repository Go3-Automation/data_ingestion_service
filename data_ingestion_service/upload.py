"""Module for uploading files to DIIP API using presigned S3 URLs."""

__all__ = ["DIIPUploader"]

import requests
import io
import logging
from typing import Union, BinaryIO
from datetime import datetime, timedelta
from botocore.response import StreamingBody

logger = logging.getLogger(__name__)


class DIIPUploader:
    """
    A context manager for uploading files to S3 via DIIP ingest API. Uses partner and entity names to create the upload URL.
    The upload session is initialized when entering the context and completed when exiting.
    Usage example:
        with DIIPUploader(base_url, api_key) as uploader:
            uploader.upload_file(entity_name, file_path)
    Attributes:
        - base_url (str): The base URL of the DIIP API. It is different per environment.
        - api_key (str): The API key for authentication received from TV3 as secret.
    """

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the uploader.

        Args:
            base_url (str): The base URL of the DIIP API.
            api_key (str): The API key for authentication.
        """
        self.base_url: str = base_url
        self.api_key: str = api_key
        self.data_package_id: str | None = None
        self._entity_url_cache: dict[str, tuple[dict, datetime]] = {}

    def __enter__(self) -> "DIIPUploader":
        """
        Enter the context manager and initialize the upload session.

        Returns:
            DIIPUploader: The uploader instance.
        """
        self.data_package_id = self._initialize_upload()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the context manager and complete the upload session.
        """
        if self.data_package_id:
            self._complete_upload()
        if exc_type:
            logger.error(f"An error occurred: {exc_value}")
        logger.info("Exiting DIIPUploader context.")

    def upload_file(self, entity_name: str, file: str | BinaryIO | StreamingBody, file_name: str = None):
        """
        Upload a file to the DIIP API on an open session.

        Args:
            entity_name (str): The name of the entity to associate with the file (e.g., table name, source name, report name).
            file (str | BinaryIO | StreamingBody): The file to upload. Can be:
                - file path (str): File will be read locally and sent to S3.
                - object (BinaryIO): An in-memory file object (e.g., already open file).
                - object (StreamingBody): An object from boto3 S3 client (e.g., response from get_object).
            file_name (str): File name to be used for the file on the destination after upload.
                             Optional for the file (str).
                             Required if `file` is a BinaryIO or StreamingBody object as there is no name associated.
        """
        entity_url = self._get_diip_upload_entity_url(self._clean_name_for_s3(entity_name))

        if isinstance(file, str):  # Local file path
            file_name = file_name or self._extract_file_name(file)
            with open(file, "rb") as f:
                self._upload_to_s3(f, entity_url, file_name)
        elif isinstance(file, (BinaryIO, StreamingBody)):  # In-memory or StreamingBody
            if not file_name:
                raise ValueError("file_name must be provided when uploading a BinaryIO or StreamingBody object.")
            if isinstance(file, StreamingBody):
                file = self._convert_streaming_body_to_bytesio(file)
            self._upload_to_s3(file, entity_url, file_name)
        else:
            raise TypeError("file must be a file path (str), a BinaryIO object, or a StreamingBody object.")

    def _initialize_upload(self) -> str:
        """Initialize the upload session and return the dataPackageId. It is happening every time the context manager is entered."""
        response = self._api_call("/upload/init")
        logger.info(f"Initialized upload session with dataPackageId: {response['dataPackageId']}")
        return response["dataPackageId"]

    def _complete_upload(self):
        """Complete the upload session. It is happening every time the context manager is exited."""
        self._api_call(f"/upload/{self.data_package_id}/complete")
        logger.info(f"Upload session completed for dataPackageId: {self.data_package_id}")

    def _get_diip_upload_entity_url(self, entity_name: str) -> dict:
        """Get a DIIP URL for uploading a file, using a cached URL if valid. This is done once per entity."""
        if entity_name in self._entity_url_cache:
            cached_url, expiration_time = self._entity_url_cache[entity_name]
            if datetime.now() < expiration_time:
                logger.info(f"Reusing cached DIIP uploading URL for entity: {entity_name}")
                return cached_url

        response = self._api_call(f"/upload/{self.data_package_id}/entity/{entity_name}")
        entity_url = response["presignedUrlData"]
        self._entity_url_cache[entity_name] = (entity_url, datetime.now() + timedelta(minutes=55))
        logger.info(f"Generated and cached entity URL for entity: {entity_name}")
        return entity_url

    def _upload_to_s3(self, file_obj: BinaryIO, entity_url: dict, file_name: str):
        """Upload a file to S3 using the provided entity URL."""
        response = requests.post(
            entity_url["url"],
            data=entity_url["fields"],
            files={"file": (file_name, file_obj)}
        )
        if response.status_code == 204:
            logger.info(f"File {file_name} uploaded successfully.")
        else:
            logger.error(f"Failed to upload file {file_name}. Status: {response.status_code}, Reason: {response.text}")
            raise Exception(f"Failed to upload file {file_name}")

    def _api_call(self, endpoint: str, method: str = "POST", payload: dict | None = None) -> dict:
        """Make an API call to the specified endpoint."""
        url = f"{self.base_url}{endpoint}"
        headers = {"x-api-key": self.api_key}
        response = requests.request(method, url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _clean_name_for_s3(entity_name: str) -> str:
        """Sanitize the entity name by replacing spaces and dashes with underscores."""
        return entity_name.replace(" ", "_").replace("-", "_")

    @staticmethod
    def _extract_file_name(file_path: str) -> str:
        """Extract the file name from a file path."""
        return file_path.split("/")[-1]

    @staticmethod
    def _convert_streaming_body_to_bytesio(streaming_body: StreamingBody) -> io.BytesIO:
        """Convert a StreamingBody object to a BytesIO object."""
        file_content = io.BytesIO(streaming_body.read())
        file_content.seek(0)
        return file_content