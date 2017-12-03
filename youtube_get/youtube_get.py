#!/usr/bin/env python
# PYTHON ARG_COMPLETE_OK
"""
Download mp3/mp4 content from a youtube playlist
"""

from __future__ import print_function
from __future__ import unicode_literals

import os
import pickle
import sys
import argparse
import argcomplete
import youtube_dl

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from .get_port import find_free_port

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
HOME = os.getenv("HOME")
CLIENT_SECRETS_FILE = HOME + "/.youtubecreds"
STORAGE = HOME + "/.youtubesaved"

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
    try:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    except FileNotFoundError:
        sys.exit("Unable to find credentials file {0}".format(CLIENT_SECRETS_FILE))
    try:
        credentials = pickle.load(open(STORAGE, "rb"))
    except (EOFError, IOError):
        credentials = None
    if credentials is None:
        credentials = flow.run_local_server(port=find_free_port())
        pickle.dump(credentials, open(STORAGE, "wb"))
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials)

def remove_non_ascii(text):
    """Remove characters that are not fat-32 friendly for filename """

    return ''.join(i for i in text if (i == ' ') or (ord(i) < 123 and ord(i) > 64) \
            or (ord(i) > 45 and ord(i) < 57)).strip()

def main():
    """
    Main module
    When running locally, disable OAuthlib's HTTPs verification. When
    running in production *do not* leave this option enabled.
    """

    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


    parser = argparse.ArgumentParser('Youtube Ripper')
    parser.add_argument('-c', '--codec', required=True,
                        action='store', help='mp3 or mp4')
    parser.add_argument('-o', '--output_dir', required=True,
                        action='store', help='output_dir')
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    if args.codec not in ('mp3', 'mp4'):
        parser.print_help()
        sys.exit(1)

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
        save_dir = args.output_dir + '/' + playlist[1]
        try:
            os.mkdir(save_dir)
        except OSError:
            pass
        urls = ['https://youtu.be/{0}'.format(item[0]) for item in videos]
        for video in urls:
            try:
                with youtube_dl.YoutubeDL() as ydl:
                    info_dict = ydl.extract_info(video, download=False)
                    title = remove_non_ascii(info_dict.get('title', None))
                if 'mp3' in args.codec:
                    ydl_opts = {'outtmpl': '{0}/{1}.%(ext)s'.format(save_dir, title),
                                'format': 'bestaudio/best',
                                'postprocessors': [{
                                    'key': 'FFmpegExtractAudio',
                                    'preferredcodec': args.codec,
                                    'preferredquality': '192'}],
                               }
                else:
                    ydl_opts = {'outtmpl': '{0}/{1}.%(ext)s'.format(save_dir, title)}
                print(ydl_opts)
                print(urls)
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video])
            except youtube_dl.utils.DownloadError:
                print("Skipping video...")


if __name__ == '__main__':
    main()
