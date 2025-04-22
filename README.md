# data_ingestion_service/data_ingestion_service/README.md

# Data Ingestion Service

A Python package for uploading files to the DIIP API using presigned S3 URLs.  
This package provides a context manager class, `DIIPUploader`, that handles session initialization, file upload, and session completion for you.

---

## What is this for?

This package is designed for organizations that need to upload data files to the DIIP platform securely and efficiently.  
It abstracts away the details of authentication, session management, and S3 presigned URL handling.

---

## Installation

Clone the repository and install in editable mode (recommended for development):

```bash
git clone https://github.com/your-org/data_ingestion_service.git
cd data_ingestion_service
pip install -e .
```

Or install directly from Git:

```bash
pip install git+https://github.com/your-org/data_ingestion_service.git
```

---

## Usage

### 1. Import the uploader

```python
from data_ingestion_service.upload import DIIPUploader
```

### 2. Set your DIIP API credentials

- `base_url`: The base URL of the DIIP API (provided by DIIP administrator).
- `api_key`: Your DIIP API key (keep this secret) Provided by the DIIP administrator. API key shall not be stored in the documentation. Shall be loaded from paramteter store as secret or be given in the Enviromental variables.

### 3. Upload a file using the context manager

```python
base_url = "https://ingest-api.uat.diip.go3.tv"
api_key = "your-api-key-loaded-from-env-variables"

with DIIPUploader(base_url=base_url, api_key=api_key) as uploader:
    uploader.upload_file(
        # entity_name: Logical name for your data (e.g., table or report) 
        # Agree with DIIP adinistrator, what is be best way to store data. 
        # It will have impact on the data analysis down the data stream
        entity_name="example_entity",
        
        # file: file with path to upload. the file name will be used as 
        # target file name, unless file_name is provided
        file="path/to/your/file.csv"

        # optional file name (for files) if not provided the original file_name will be used.
        file_name="updated_file_name.csv"
    )
```

#### Uploading an in-memory file or S3 StreamingBody

If you have a file-like object (e.g., `io.BytesIO` or `StreamingBody`), provide the mandatory `file_name` argument in case of file less upload:

```python
import io

with DIIPUploader(base_url=base_url, api_key=api_key) as uploader:
    file_obj = io.BytesIO(b"some,data,to,upload\n1,2,3,4")
    uploader.upload_file(
        # entity_name: Logical name for your data (e.g., table or report) 
        # Agree with DIIP adinistrator, what will be best way to store data. 
        # It will have impact on the data analysis down the data stream
        entity_name="example_entity",

        # file may be object BytesIO or StreamingBody instead of file name.
        # In that case file_name is mandatory.
        file=file_obj,
        
        # file_name is mandatory in case of BytesIO or StreamingBody 
        # as there is not file_name to be used as defautl
        file_name="data.csv"
    )
```

---

## How it works

- When you enter the `with DIIPUploader(...) as uploader:` block, a session is initialized with the DIIP API.
- You can call `uploader.upload_file(...)` as many times as needed within the block/session you may use different entities.
- When you exit the block, the session is completed and finalized with the DIIP API.

---

## Running Tests

To run the tests, use:

```bash
pytest tests/
```

---

## License

This project is licensed under a custom Go3 license. See the [LICENSE](LICENSE) file for details.

---

**Need help?**  
Contact your Go3 administrator or the package maintainer for support and API access.
