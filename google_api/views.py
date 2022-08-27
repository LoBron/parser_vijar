from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from os.path import exists
from time import sleep
from typing import Dict, Union, List, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

from settings import GOOGLE_CREDENTIALS_NAME, GOOGLE_FOLDER_NAME, GOOGLE_SCOPES


class GoogleWorker:
    def __init__(self):
        self.__api = GoogleAPI()

    def search_files(self, category_id: Union[int, None] = None) -> List[str]:
        return self.__api.search_files(category_id)

    def delete_file(self, file_id: str) -> Union[str, None]:
        return self.__api.delete_file(file_id)

    def upload_file(self,
                    item_id: int,
                    key: str,
                    file: Union[BytesIO, None],
                    file_metadata: Dict[str, str]) -> dict:
        return self.__api.upload_file(item_id, key, file, file_metadata)



class GoogleAPI:
    def __init__(self):
        self.__credentials = google_auth()
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

    def _create_folder(self, folder_name: str, google_credentials: Credentials) -> Union[str, None]:
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
                                                       'files(id, name, permissions)',
                                                pageToken=page_token).execute()
                print(len(response.get('files', [])))
                for file in response.get('files', []):
                    # Process change

                    print(F'Found file: {file.get("name")}, {file.get("id")}, {file.get("permissions")}')
                files.extend(response.get('files', []))
                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break

            # for file in files:
            #     print(file.get("id"))
            #     print(file.get("name"))
            #     print(file.get("permissions"))
            #     print()

        except HttpError as error:
            print(F'An error occurred: {error}')
        return files

    def delete_file(self, file_id: str) -> Union[str, None]:
        return file_id

    def upload_file(self,
                     item_id: int,
                     key: str,
                     image: Union[BytesIO, None],
                     file_metadata: Dict[str, str]) -> dict:
        data = {'item_id': item_id, 'key': key, 'fileId': None}
        if image:
            # create gmail api client
            service = build('drive', 'v3', credentials=self.__credentials)
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
                user_permission = {'type': 'anyone', 'value': 'anyone', 'role': 'reader'}
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
#
# def get_photos_id_list(photos_response_list: List[dict],
#                        folder_id: str,
#                        google_credentials: Credentials
#                        ) -> Tuple[int, List[dict]]:
#     photos_data_list = []
#     count_photos = 0
#     if photos_response_list:
#         try:
#             with ThreadPoolExecutor(max_workers=30) as executor:
#                 future_list = [executor.submit(upload_image,
#                                                item_id=response.get('item_id'),
#                                                key=response.get('key'),
#                                                image=BytesIO(response.get('photo')) if response.get('photo') else None,
#                                                google_credentials=google_credentials,
#                                                file_metadata={'name': response.get('name'), 'parents': [folder_id]},
#                                                ) for response in photos_response_list]
#                 for future in as_completed(future_list):
#                     result = future.result()
#                     photos_data_list.append(result)
#                     if result.get('fileId'):
#                         count_photos += 1
#         except Exception as ex:
#             photos_data_list.clear()
#             count_photos = 0
#             print(f'Exception - {ex}')
#     return count_photos, photos_data_list


class FolderIdError(Exception):
    """Google drive folder not created."""
    pass


def google_auth() -> Union[Credentials, None]:
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


if __name__ == '__main__':
    worker = GoogleWorker()
    # creds = google_auth()
    # search_items('1Dk0fpGCaqIGc0Op7p1Fnr8uFwSszIe3n', creds)
