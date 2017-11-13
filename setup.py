#!/usr/bin/env python

"""
Setup script for youtube-downloader- an mp3/mp4 youtube downloader
"""

from setuptools import setup

with open('requirements.txt', 'r') as reqs_file:
    REQS = reqs_file.readlines()
VER = '0.1'

setup(
    name='youtube_get',
    packages=['youtube_get'],
    version=VER,
    description='an mp3/mp4 youtube downloader',
    author='Amro Diab',
    author_email='adiab@linuxmail.org',
    url='https://github.com/adiabuk/youtube-downloader',
    download_url=('https://github.com/adiabuk/youtube-downloader/archive/{0}.tar.gz' .format(VER)),
    keywords=['youtube'],
    install_requires=REQS,
    entry_points={'console_scripts':['youtube_get=youtube_get.youtube_get:main']},
    classifiers=[],
)
