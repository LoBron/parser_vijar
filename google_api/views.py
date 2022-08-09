from io import BytesIO
from os.path import exists
from typing import Dict, Union

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload


def google_upload_image(item_id: int,
                        key: str,
                        image: BytesIO,
                        google_credentials: Credentials,
                        file_metadata: Dict[str, str],
                        user_permission: Dict[str, str]) -> dict:
    data = {'item_id': item_id, 'key': key, 'fileId': None}
    try:
        # create gmail api client
        service = build('drive', 'v3', credentials=google_credentials)
        media = MediaIoBaseUpload(image, mimetype='image/jpg')
        file = service.files().create(body=file_metadata, media_body=media).execute()
        fileId = file.get("id")
        service.permissions().create(fileId=fileId, body=user_permission).execute()
        data['fileId'] = fileId
    except HttpError as error:  # HttpError
        print(F'An error occurred: {error}')
    return data


def google_auth():
    """Shows basic usage of the Drive v3 API.
      Prints the names and ids of the first 10 files the user has access to.
      """
    creds = None
    SCOPES = ['https://www.googleapis.com/auth/drive']
    # The file credentials.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def google_search_folder(folder_name: str, google_credentials: Credentials) -> Union[str, None]:
    """Search file in drive location

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    folder_id = None
    try:
        # create drive api client
        service = build('drive', 'v3', credentials=google_credentials)
        files = []
        page_token = None
        while True:
            # pylint: disable=maybe-no-member
            response = service.files().list(q="mimeType = 'application/vnd.google-apps.folder'",
                                            spaces='drive',
                                            fields='nextPageToken, '
                                                   'files(id, name)',
                                            pageToken=page_token).execute()
            # for file in response.get('files', []):
            #     # Process change
            #     print(F'Found file: {file.get("name")}, {file.get("id")}')
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        for file in files:
            if file.get("name") == folder_name:
                folder_id = file.get("id")
                break

    except HttpError as error:
        print(F'An error occurred: {error}')

    return folder_id


def google_create_folder(folder_name: str, google_credentials: Credentials) -> Union[str, None]:
    """ Create a folder and prints the folder ID
    Returns : Folder Id

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    folder_id = None
    try:
        # create drive api client
        service = build('drive', 'v3', credentials=google_credentials)
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        # pylint: disable=maybe-no-member
        file = service.files().create(body=file_metadata, fields='id'
                                      ).execute()
        folder_id = file.get("id")

    except HttpError as error:
        print(F'An error occurred: {error}')

    return folder_id
