#!/usr/bin/env python
"""
Download mp3/mp4 content from a youtube playlist
"""

from __future__ import print_function
import os

from get_port import find_free_port
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import youtube_dl

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
HOME = os.getenv("HOME")
CLIENT_SECRETS_FILE = HOME + "/.youtubecreds"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# Remove keyword arguments that are not set
def remove_empty_kwargs(**kwargs):
    """remove kwawg from kwargs if it is an empty string"""
    good_kwargs = {}
    if kwargs is not None:
        for key, value in kwargs.items():
            if value:
                good_kwargs[key] = value
    return good_kwargs

def playlists_list_mine(service, **kwargs):
    """ List all playlists for current authenticated user """
    playlists = []
    kwargs = remove_empty_kwargs(**kwargs)
    results = service.playlists().list(**kwargs).execute()

    for item in results['items']:
        playlists.append((item['id'], item['snippet']['title']))

    return playlists

def get_playlist_items(service, **kwargs):
    """ get a list of videos in a playlist from a playlist ID"""

    videos = []
    kwargs = remove_empty_kwargs(**kwargs)
    results = service.playlistItems().list(**kwargs).execute()

    for item in results['items']:
        videos.append((item['contentDetails']['videoId'], item['snippet']['title']))
    return videos

def get_authenticated_service():
    """
    Authenticate with  Youtube API using OAUTH
    """

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=find_free_port())
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def main():
    """
    Main module
    When running locally, disable OAuthlib's HTTPs verification. When
    running in production *do not* leave this option enabled.
    """

    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    service = get_authenticated_service()

    playlists = playlists_list_mine(service, part='snippet,contentDetails',
                                    mine=True,
                                    maxResults=25,
                                    onBehalfOfContentOwner='',
                                    onBehalfOfContentOwnerChannel='')
    # get vidio list:
    for playlist in playlists:
        videos = get_playlist_items(service, part='snippet,contentDetails',
                                    maxResults=25,
                                    playlistId=playlist[0])
        try:
            os.mkdir(playlist[1])
        except OSError:
            pass
        urls = ['https://youtu.be/{0}'.format(item[0]) for item in videos]
        codec = 'mp3'

        if 'mp3' in codec:
            ydl_opts = {'outtmpl': '{0}/%(title)s.%(ext)s'.format(playlist[1]),
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': codec,
                            'preferredquality': '192'}],
                       }
        else:
            ydl_opts = {'outtmpl': '{0}/%(title)s.%(ext)s'.format(playlist[1])}

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(urls)

if __name__ == '__main__':
    main()
