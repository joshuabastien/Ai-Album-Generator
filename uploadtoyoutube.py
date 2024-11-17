from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle

# Scopes required for the YouTube Data API
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service(token_name='token.pickle'):
    credentials = None
    if os.path.exists(token_name):
        with open(token_name, 'rb') as token:
            credentials = pickle.load(token)
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            credentials = flow.run_local_server(port=0)
        with open(token_name, 'wb') as token:
            pickle.dump(credentials, token)
    return build('youtube', 'v3', credentials=credentials)

def upload_video(youtube, file, title, description, category, tags):
    body = {
        'snippet': {
            'title': title,
            'description': description,
            'tags': tags,
            'categoryId': category
        },
        'status': {
            'privacyStatus': 'public'
        }
    }

    media = MediaFileUpload(file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part='snippet,status',
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f'Uploaded {int(status.progress() * 100)}%')

    print('Upload Complete!')
    return response

if __name__ == '__main__':
    youtube = get_authenticated_service()
    file = 'video/combined_video.mp4'
    title = 'Cafe Jazz'
    description = 'Jazz music to study and relax.'
    category = '22'  # See https://developers.google.com/youtube/v3/docs/videoCategories/list
    tags = ['Jazz', 'lofi']

    upload_video(youtube, file, title, description, category, tags)