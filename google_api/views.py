from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from os.path import exists
from time import sleep
from typing import Dict, Union, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

from settings import GOOGLE_CREDENTIALS_NAME


def get_photos_id_list(photos_response_list: List[dict],
                       folder_id: str,
                       google_credentials: Credentials
                       ) -> List[dict]:
    photos_data_list = []
    if photos_response_list:
        try:
            with ThreadPoolExecutor(max_workers=50) as executor:
                user_permission = {'type': 'anyone', 'value': 'anyone', 'role': 'reader'}
                future_list = [executor.submit(upload_image,
                                               item_id=response.get('item_id'),
                                               key=response.get('key'),
                                               image=BytesIO(response.get('photo')) if response.get('photo') else None,
                                               google_credentials=google_credentials,
                                               file_metadata={'name': response.get('name'), 'parents': [folder_id]},
                                               user_permission=user_permission
                                               ) for response in photos_response_list]
                for future in as_completed(future_list):
                    photos_data_list.append(future.result())
        except Exception as ex:
            photos_data_list.clear()
            print(f'Exception - {ex}')
    return photos_data_list


def upload_image(item_id: int,
                 key: str,
                 image: Union[BytesIO, None],
                 google_credentials: Credentials,
                 file_metadata: Dict[str, str],
                 user_permission: Dict[str, str]) -> dict:
    data = {'item_id': item_id, 'key': key, 'fileId': None}
    if image:
        # create gmail api client
        service = build('drive', 'v3', credentials=google_credentials)
        media = MediaIoBaseUpload(image, mimetype='image/jpg')
        fileId = None
        n = 1
        t = 0.5
        while n <= 5:
            try:
                file = service.files().create(body=file_metadata, media_body=media).execute()
                fileId = file.get("id")
            except HttpError as error:
                if error.resp.status == '403' and error.reason == 'User rate limit exceeded.':
                    sleep(t)
                    n += 1
                    t *= 2
                else:
                    break
            else:
                break
        if fileId:
            n = 1
            t = 0.5
            while n <= 5:
                try:
                    service.permissions().create(fileId=fileId, body=user_permission).execute()
                except HttpError as error:
                    if error.resp.status == '403' and error.reason == 'User rate limit exceeded.':
                        sleep(t)
                        n += 1
                        t *= 2
                    else:
                        break
                else:
                    data['fileId'] = fileId
                    break
    return data


def google_auth() -> Union[Credentials, None]:
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
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_NAME, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def search_folder(folder_name: str, google_credentials: Credentials) -> Union[str, None]:
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


def create_folder(folder_name: str, google_credentials: Credentials) -> Union[str, None]:
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
