from __future__ import print_function
from os.path import exists
from io import BytesIO

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload



def auth():
    """Shows basic usage of the Drive v3 API.
      Prints the names and ids of the first 10 files the user has access to.
      """
    creds = None
    SCOPES = ['https://www.googleapis.com/auth/drive']
    # The file credentials.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if exists('credentials.json'):
        creds = Credentials.from_authorized_user_file('credentials.json', SCOPES)
        print(creds)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('credentials.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def upload_image(name: str, photo: bytes, creds: Credentials) -> str:
    image = BytesIO(photo)
    try:
        # create gmail api client
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': name}
        user_permission = {'type': 'anyone', 'value': 'anyone', 'role': 'reader'}
        media = MediaIoBaseUpload(image,
                                  mimetype='image/jpg')
        file = service.files().create(body={'name': name}, media_body=media).execute()
        fileId = file.get("id")
        service.permissions().create(fileId=fileId,
                                     body=user_permission).execute()
        return fileId

    except HttpError as error:
        print(F'An error occurred: {error}')
        return None


def get_file(creds):
    try:
        # create gmail api client
        service = build('drive', 'v3', credentials=creds)
        id_ = "1QVMNUwbp41-aCqwo-vZlub_phE8sGxZZ"
        file = service.files().get(fileId=id_).execute()
        print(file)
        file1 = service.permissions().get(fileId=id_).execute()
        print(file1)

    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None


# if __name__ == '__main__':
#     auth()
#     create_file(auth())
# files = get_file(auth())
