# data_ingestion_service/data_ingestion_service/README.md

# Data Ingestion Service

A service for data ingestion via the DIIP API.

## Installation

To install the package from Git, use the following command:

```
pip install git+https://github.com/your-org/data_ingestion_service.git
```

## Usage

Here is an example of how to use the `diip_uploader` class:

```python
from data_ingestion_service.upload import diip_uploader

base_url = "https://ingest-api.uat.diip.go3.tv"
api_key = "your-api-key"

with diip_uploader(base_url=base_url, api_key=api_key) as session:
    session.upload_file(entity_name="example_entity", file="path/to/your/file.csv")
```

## Running Tests

To run the tests, you can use the following command:

```
pytest tests/
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.

# OLD REDME TO BE UPDATES
# Data Ingestion Service (DIS) File Uploader

This project provides a Python script to upload files to an Amazon S3 bucket using pre-signed URLs. The script uses the `requests` library to handle HTTP requests and the built-in `logging` module to log the status of each file upload.

## Table of Contents

- [Data Ingestion Service (DIS) File Uploader](#data-ingestion-service-dis-file-uploader)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Configuration](#configuration)
    - [Credentials](#credentials)
    - [Logging](#logging)
    - [Environment](#environment)
  - [License](#license)

## Prerequisites

- Python 3.x
- `requests` library

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/s3-file-uploader.git
    cd s3-file-uploader
    ```

2. Install the required dependencies:
    ```sh
    pip install requests
    ```

## Usage

To use the `upload_files_to_s3` function, you need to provide a list of file paths to be uploaded and a response dictionary containing the pre-signed URL and fields required for the upload, for example:

```sh
python upload.py Reports report1.csv report2.csv
```

## Configuration

### Credentials

Create `credentials.py` which will include the definition of all environments, for example:

```python
dis = {
    'UAT': {
        'url': 'https://ingest-uat.api',
        'token': '2416b808-4698-4ad7-8043-b7613c8b9b3c'
    },
    'PROD': {
        'url': 'https://ingest.api',
        'token': '52c75128-fe02-46a9-8803-5c8d96c467e9'
    }
}
```

### Logging

Configure the logging settings at the beginning of your script. The script uses the `logging` module to log messages at different severity levels:

- `INFO`: Logs successful file uploads.
- `ERROR`: Logs failed file uploads with status code and reason.
- `EXCEPTION`: Logs exceptions that occur during file uploads with traceback.

### Environment

Configure the environment. The script uses 'UAT' and 'PROD' environments, but additional environments may be added in `credentials.py`.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
