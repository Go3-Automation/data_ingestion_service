import sys
import requests
import credentials
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

environment = 'UAT' # Change to PROD when ready


def dis_api_call(url, payload, headers):
    """
    Makes a POST request to the specified URL with the given payload and headers.

    Parameters:
    url (str): The endpoint URL to which the POST request is made.
    payload (dict): The JSON payload to be sent in the body of the POST request.
    headers (dict): The headers to be included in the POST request.

    Returns:
    dict: A dictionary containing the status code and response data. If the request is successful,
          the dictionary will contain 'status_code' set to 200 and 'response' with the JSON response.
          If the request fails, it will contain 'status_code' with the error code.
    """
    try:
        response = requests.request("POST", url, headers=headers, json=payload)
        if response.status_code == 200:
            logger.debug("API call successful ", response.text)
            return {'status_code': 200, 'response': response.json()}
        else:
            logger.error("Error: ", response.text)
            return {'status_code': response.status_code}
    except Exception as e:
        logger.error("Error: ", e)
        return {'status_code': 500}
    

def upload_init():
    """
    Initialize upload session and generate dataPackageId

    Returns:
        dataPackageId: The ID of data package
    """
    url = credentials.dis['UAT']['url'] + "/upload/init"
    payload = {}
    headers = {
        'x-api-key': credentials.dis['UAT']['token']
    }
    return dis_api_call(url, payload, headers)
 

def generate_upload_url(data_package_id, entity_name):
    """
    Generate upload url for given dataPackageId and Entity

    Args:
        data_package_id (string): The data package ID from initialization
        entity_name (string): The name of uploaded entity

    Returns:
        presignedUrlData: The presigned url data
    """
    url = credentials.dis['UAT']['url'] + f"/upload/{data_package_id}/entity/{entity_name}"
    payload = {}
    headers = {
        'x-api-key': credentials.dis['UAT']['token']
    }
    return dis_api_call(url, payload, headers)


def complete_upload(data_package_id):
    """
    Complete upload session and block given dataPackageId from further upload.

    Args:
        data_package_id (string): The id of the data package
    """
    url = credentials.dis['UAT']['url'] + f"/upload/{data_package_id}/complete"
    payload = {}
    headers = {
        'x-api-key': credentials.dis['UAT']['token']
    }
    return dis_api_call(url, payload, headers)

 
def upload_files_to_s3(files_to_upload, url_data):
    """
    Uploads a list of files to an S3 bucket using pre-signed URLs.

    Parameters:
    files_to_upload (list): A list of file paths to be uploaded.
    url_data (dict): A dictionary containing the pre-signed URL and fields required for the upload.
                     The dictionary should have keys 'url' and 'fields'.

    Returns:
    None: This function does not return any value. It prints the status of each file upload.
    """
    for file in files_to_upload:
        files = {"file": open(file, "rb")}
        response = requests.post(url_data["url"], data=url_data["fields"], files=files)
 
        if response.status_code == 204:
            logger.info(f"File {file} uploaded successfully.")
        else:
            logger.error(f"Failed to upload file {file}. Status code: {response.status_code}, Reason: {response.text}")


if __name__ == "__main__":
    # Verify if the call has enough arguments, the minimum is the entity name and the list of files
    if len(sys.argv) < 3:
        print(f"Usage: python {sys.argv[0]} <entity_name> <file1> <file2> ...")
        sys.exit(1)
        
    # Initialize upload
    result = upload_init()
    if result['status_code'] == 200:
        data_package_id = result['response']['dataPackageId']
        entity_name = sys.argv[1]
        logger.info(f"Generating upload url for {entity_name} and id {data_package_id}")
        result = generate_upload_url(data_package_id, entity_name)
        if result['status_code'] == 200:
            # Iterate through the sys arguments
            files_to_upload = []
            for file in sys.argv[2:]:
                files_to_upload.append(file)
            logger.info(f"Uploading files {files_to_upload}") 
            upload_files_to_s3(files_to_upload, result['response']['presignedUrlData'])
            logger.info(f"Completing upload for {data_package_id}")
            result = complete_upload(data_package_id)