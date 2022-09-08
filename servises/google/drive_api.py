from io import BytesIO
from os.path import exists
from time import sleep
from typing import Union, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from requests import get

from settings import GOOGLE_CREDENTIALS_NAME, GOOGLE_FOLDER_NAME, GOOGLE_SCOPES


class FolderIdError(Exception):
    """Google drive folder not created."""
    pass


class DriveAPI:
    def __init__(self):
        self.__credentials = self._google_auth()
        self.__folder_id = self._search_folder(GOOGLE_FOLDER_NAME)
        if not self.__folder_id:
            self.__folder_id = self._create_folder(GOOGLE_FOLDER_NAME)
            if not self.__folder_id:
                raise FolderIdError

    def _search_folder(self, folder_name: str) -> Union[str, None]:
        """Search folder in drive location
        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """
        folder_id = None
        try:
            # create drive api client
            service = build('drive', 'v3', credentials=self.__credentials)
            files = []
            page_token = None
            while True:
                response = service.files().list(q="mimeType = 'application/vnd.google-apps.folder' and trashed != True",
                                                spaces='drive',
                                                fields='nextPageToken, '
                                                       'files(id, name)',
                                                pageToken=page_token).execute()
                # for file in response.get('files', []):
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

    def _create_folder(self, folder_name: str) -> Union[str, None]:
        """ Create a folder and prints the folder ID
        Returns : Folder Id

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """
        folder_id = None
        try:
            # create drive api client
            service = build('drive', 'v3', credentials=self.__credentials)
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

    def search_files(self, category_id: Union[int, None] = None):
        """Search file in drive location

        Load pre-authorized user credentials from the environment.
        TODO(developer) - See https://developers.google.com/identity
        for guides on implementing OAuth2 for the application.
        """
        files = []
        try:
            # create drive api client
            service = build('drive', 'v3', credentials=self.__credentials)

            page_token = None
            while True:
                # pylint: disable=maybe-no-member
                response = service.files().list(q=f"mimeType = 'image/jpeg' and trashed = False",
                                                spaces='drive',
                                                fields='nextPageToken, '
                                                       'files(id, name)',
                                                pageToken=page_token).execute()
                for file in response.get('files', []):
                    # Process change
                    files.append(file.get("id"))
                files.extend(response.get('files', []))
                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break
        except HttpError as error:
            print(F'An error occurred: {error}')
        return files

    def delete_file(self, file_id: str) -> Union[str, None]:
        return file_id

    def upload_file(self, id_: int, data: BytesIO, name: str, mimetype: str) -> Dict[int, Union[str, None]]:
        fileId = {id_: None}
        # create gmail api client
        file_metadata = {'name': name, 'parents': [self.__folder_id]}
        service = build('drive', 'v3', credentials=self.__credentials)
        media = MediaIoBaseUpload(data, mimetype=mimetype)
        n = 1
        t = 0.5
        while True:
            try:
                file = service.files().create(body=file_metadata, media_body=media).execute()
                Id = file.get("id")
            except HttpError as error:
                if n <= 5:
                    if error.resp.status == '403' and error.reason == 'User rate limit exceeded.':
                        sleep(t)
                        n += 1
                        t *= 2
                    else:
                        Id = None
                        break
            else:
                break
        if Id:
            n = 1
            t = 0.5
            user_permission = {'type': 'anyone', 'value': 'anyone', 'role': 'reader'}
            while n <= 5:
                try:
                    service.permissions().create(fileId=Id, body=user_permission).execute()
                except HttpError as error:
                    if error.resp.status == '403' and error.reason == 'User rate limit exceeded.':
                        sleep(t)
                        n += 1
                        t *= 2
                    else:
                        break
                else:
                    fileId[id_] = Id
                    break
        return fileId

    @staticmethod
    def _google_auth() -> Union[Credentials, None]:
        """Shows basic usage of the Drive v3 API.
          Prints the names and ids of the first 10 files the user has access to.
          """
        creds = None
        # The file credentials.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', GOOGLE_SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_NAME, GOOGLE_SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return creds


# def delete_images(self, category_id: int) -> List[str]:
#     deleted_files = []
#     files_id_list = self._search_files()
#     with ThreadPoolExecutor(max_workers=30) as executor:
#         future_list = [executor.submit(self._delete_file, file_id) for file_id in files_id_list]
#         for future in as_completed(future_list):
#             result = future.result()
#             if result:
#                 deleted_files.append(result)
#     return deleted_files




# if __name__ == '__main__':
#     photo = get('https://viyar.ua/upload/resize_cache/photos/300_300_1/ph28253.jpg').content
#     worker = GoogleAPI()
#     id_ = worker.upload_file(1, BytesIO(photo), 'ph28253', 'image/jpg')
#     print(id_)
