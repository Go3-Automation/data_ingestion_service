import requests
import io
import logging
from typing import Union, BinaryIO
from datetime import datetime, timedelta
from botocore.response import StreamingBody

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class diip_uploader:
    """
    A context manager for uploading files to S3 via presigned URLs provided by the DIIP API.
    """

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the uploader.

        Args:
            base_url (str): The base URL of the DIIP API.
            api_key (str): The API key for authentication.
        """
        self.base_url = base_url
        self.api_key = api_key
        self.data_package_id: Union[str, None] = None
        self._presigned_url_cache: dict[str, tuple[dict, datetime]] = {}

    def __enter__(self) -> "diip_uploader":
        """
        Enter the context manager and initialize the upload session.

        Returns:
            diip_uploader: The uploader instance.
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
        logger.info("Exiting diip_uploader context.")

    def upload_file(self, entity_name: str, file: Union[str, BinaryIO, StreamingBody], file_name: str = None):
        """
        Upload a file to the DIIP API.

        Args:
            entity_name (str): The name of the entity to associate with the file.
            file (Union[str, BinaryIO, StreamingBody]): The file to upload. Can be a file path (str),
                                                        an in-memory file object (BinaryIO), or a StreamingBody object.
            file_name (str): Optional file name for logging purposes. Required if `file` is a BinaryIO or StreamingBody object.
        """
        presigned_url = self._get_presigned_url(self._sanitize_entity_name(entity_name))

        if isinstance(file, str):  # Local file path
            file_name = file_name or self._extract_file_name(file)
            with open(file, "rb") as f:
                self._upload_to_s3(f, presigned_url, file_name)
        elif isinstance(file, (BinaryIO, StreamingBody)):  # In-memory or StreamingBody
            if not file_name:
                raise ValueError("file_name must be provided when uploading a BinaryIO or StreamingBody object.")
            if isinstance(file, StreamingBody):
                file = self._convert_streaming_body_to_bytesio(file)
            self._upload_to_s3(file, presigned_url, file_name)
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

    def _get_presigned_url(self, entity_name: str) -> dict:
        """Get a presigned URL for uploading a file, using a cached URL if valid. This is done once per entity."""
        if entity_name in self._presigned_url_cache:
            cached_url, expiration_time = self._presigned_url_cache[entity_name]
            if datetime.now() < expiration_time:
                logger.info(f"Reusing cached presigned URL for entity: {entity_name}")
                return cached_url

        response = self._api_call(f"/upload/{self.data_package_id}/entity/{entity_name}")
        presigned_url = response["presignedUrlData"]
        self._presigned_url_cache[entity_name] = (presigned_url, datetime.now() + timedelta(minutes=55))
        logger.info(f"Generated and cached presigned URL for entity: {entity_name}")
        return presigned_url

    def _upload_to_s3(self, file_obj: BinaryIO, presigned_url: dict, file_name: str):
        """Upload a file to S3 using the provided presigned URL."""
        response = requests.post(
            presigned_url["url"],
            data=presigned_url["fields"],
            files={"file": (file_name, file_obj)}
        )
        if response.status_code == 204:
            logger.info(f"File {file_name} uploaded successfully.")
        else:
            logger.error(f"Failed to upload file {file_name}. Status: {response.status_code}, Reason: {response.text}")
            raise Exception(f"Failed to upload file {file_name}")

    def _api_call(self, endpoint: str, method: str = "POST", payload: dict = None) -> dict:
        """Make an API call to the specified endpoint."""
        url = f"{self.base_url}{endpoint}"
        headers = {"x-api-key": self.api_key}
        response = requests.request(method, url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _sanitize_entity_name(entity_name: str) -> str:
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