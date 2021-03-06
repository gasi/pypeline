#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
pypeline

Created by Daniel Gasienica on 2010-12-29.
Copyright (c) 2010 Daniel Gasienica. All rights reserved.
"""

VERSION = '0.0.1'

import imdb
import glob
import json
import logging
import optparse
import os
import os.path
import parser
import re
import subprocess
import tmdb
import urllib

import settings

DEFAULT_SOURCE = '~/Downloads'
DEFAULT_DESTINATION = '~/Movies/pypeline'

ENCODED_EXTENSIONS = ['m4v', 'mp4']
EXTENSIONS = ['wmv', 'avi', 'mpg', 'mpeg', 'mkv'] + ENCODED_EXTENSIONS
ILLEGAL_CHARACTERS = ['[', ']', '*', ':', '/', '<', '>', '=', ';']

IMDb = imdb.IMDb()
SERIES_OVERRIDES = {}
MOVIE_OVERRIDES = {}

BASE = os.path.dirname(os.path.abspath(__file__))
HANDBRAKE = os.path.join(BASE, '../vendor/handbrake/HandbrakeCLI')
ATOMIC_PARSLEY = os.path.join(BASE, '../vendor/atomic_parsley/AtomicParsley')

# Apple TV settings
def encode(source, target):
    with open(os.devnull, 'w') as nirvana:
        args = [HANDBRAKE,
                '-i', source,
                '-o', target,
                '-e', 'x264',
                '-q', '20.0',
                '-a', '1,1',
                '-E', 'faac,ac3',
                '-B', '160,160 -6 dpl2,auto',
                '-R', '48,Auto',
                '-D', '0.0,0.0'
                '-f', 'mp4 -4',
                '--maxWidth', '1280',
                '--optimize', '',
                '--loose-anamorphic', '',
                '-m', '',
                '-x', 'cabac=0:ref=2:me=umh:b-adapt=2:weightb=0:trellis=0:weightp=0']

        # Subtitles
        base, ext = os.path.splitext(source)
        srt_filename = base + '.srt'
        if os.path.exists(srt_filename):
            args += ['--srt-file', srt_filename]

        subprocess.call(args, stdout=nirvana, stderr=nirvana)

def get_descriptor(item):
    descriptor = None
    if 'series_title' in item:
        series_title = item['series_title'].lower()
        if series_title not in SERIES_OVERRIDES:
            movies = IMDb.search_movie(series_title)
            if not movies:
                return None
            movie = movies[0]
        else:
            movie = IMDb.get_movie(SERIES_OVERRIDES[series_title])
        IMDb.update(movie, 'episodes')
        episode = movie['episodes'][item['season']][item['episode']]
        descriptor = {'series_title': episode['series title'],
                      'title': str(episode['title']),
                      'season': int(episode['season']),
                      'episode': int(episode['episode']),
                      'year': int(episode['year']),
                      'plot': episode.get('plot', ''),
                      'cover': movie.get('full-size cover url', '')}
    else:
        title = item['title'].lower()
        if title not in MOVIE_OVERRIDES:
            movies = IMDb.search_movie(title)
            if not movies:
                return None
            movie = movies[0]
        else:
            movie = IMDb.get_movie(MOVIE_OVERRIDES[title])
        IMDb.update(movie)

        descriptor = {'title': movie['title'],
                      'plot': movie.get('plot', [''])[0],
                      'director': movie.get('director', [{'name':''}])[0].get('name', ''),
                      'year': int(movie['year']),
                      'cover': movie.get('full-size cover url', '')}

    # Find artwork on TMDb
    try:
        title = urllib.quote(descriptor.get('title').encode("utf-8"))
        url = 'http://api.themoviedb.org/2.1/Movie.search/en/json/%(api_key)s/%(title)s'
        response = urllib.urlopen(url % {'api_key': settings.TMDB_API_KEY, 'title': title})
        movie = json.loads(response.read())[0]
        cover = movie['posters'][0]['image']['url']
        descriptor['cover'] = cover
    except:
        # Never mind ;)
        pass

    return descriptor

def set_metadata(filename, descriptor):
    args = [ATOMIC_PARSLEY,
            filename,
            '--title', '%(title)s' % descriptor,
            '--year', '%(year)d' % descriptor,
            '--description', '%(plot)s' % descriptor]

    # Various filenames
    base, ext = os.path.splitext(filename)
    cover_filename = base + '.jpg'

    # Cover art
    cover_exists = bool(descriptor['cover'])
    if cover_exists:
        # Download artwork
        urllib.urlretrieve(descriptor['cover'], cover_filename)
        args +=  ['--artwork', cover_filename]

    if 'series_title' in descriptor:
        args +=  ['--album', '%(series_title)s, Season %(season)d' % descriptor,
                  '--albumArtist', '%(series_title)s' % descriptor,
                  '--artist', '%(series_title)s' % descriptor,
                  '--disknum', '1/1',
                  '--genre', '',
                  '--stik', 'TV Show',
                  '--tracknum', '%(episode)d' % descriptor,
                  '--TVShowName', '%(series_title)s' % descriptor,
                  '--TVEpisode', 'S%(season)dE%(episode)d' % descriptor,
                  '--TVSeason', '%(season)d' % descriptor,
                  '--TVEpisodeNum', '%(episode)d' % descriptor]
    else:
        args +=  ['--artist', '%(director)s' % descriptor,
                  '--genre', '',
                  '--stik', 'Movie']
    with open(os.devnull, 'w') as nirvana:
        subprocess.call(args, stdout=nirvana)

    # Delete cover art
    if cover_exists:
        os.remove(cover_filename)

    # Rename file
    temp_filename = get_target_temp_filename(filename)
    if temp_filename:
        os.remove(filename)
        os.rename(temp_filename, filename)

def get_target_temp_filename(filename):
    root, ext = os.path.splitext(filename)
    files = glob.glob(root + '-temp-*.m4v')
    temp_filename = files[0] if files else None
    return temp_filename

def get_target_filename(destination, filename, descriptor):
    target_basename = os.path.basename(os.path.splitext(filename)[0])
    target_basename = get_title(descriptor, target_basename)
    # sanitize target filename
    for char in ILLEGAL_CHARACTERS:
        target_basename = target_basename.replace(char, '')
    target = os.path.join(destination, target_basename + '.m4v')
    return target

def get_sources(path):
    sources = []
    for extension in EXTENSIONS:
        sources += glob.glob(path + '/*.' + extension)
        sources += glob.glob(path + '/**/*.' + extension)
    return sorted(sources)

def get_title(descriptor, default='Untitled'):
    if not descriptor:
        return default

    if 'series_title' in descriptor:
        return '%(series_title)s S%(season)02dE%(episode)02d' % descriptor
    elif 'title' in descriptor:
        return '%(title)s' % descriptor
    else:
        return default

def process(src, dest, encode_only=False):
    s = os.path.expanduser(src)
    d = os.path.expanduser(dest)
    if not os.path.exists(d):
        os.makedirs(d)

    sources = get_sources(s)
    for source in sources:
        item = None
        descriptor = None
        # acquire metadata
        if not encode_only:
            item = parser.parse_tv_show(source)
            if not item:
                item = parser.parse_movie(source)
            if item:
                try:
                    descriptor = get_descriptor(item)
                except:
                    print('Failed to get descriptor: %s' % item.get('title', ''))
                    descriptor = None

        # encoding
        target = get_target_filename(d, source, descriptor)
        if not os.path.exists(target):
            print('Encoding: %s' % get_title(descriptor))
            encode(source, target)

        # metadata
        if descriptor and not encode_only:
            print('Writing metadata: %s' % get_title(descriptor))
            set_metadata(target, descriptor)


def main():
    parser = optparse.OptionParser(usage='Usage: %prog [options] filename')
    parser.add_option('-s', '--source', dest='source', default=DEFAULT_SOURCE,
                      help='Source path. Default: ' + DEFAULT_SOURCE)
    parser.add_option('-d', '--destination', dest='destination',
                      default=DEFAULT_DESTINATION,
                      help='Destination path. Default: ' + DEFAULT_DESTINATION)
    parser.add_option('-e', '--encode-only', action='store_true', dest='encode_only',
                      default=False, help='Encode only. Default: ' + str(False))
    (options, args) = parser.parse_args()
    process(options.source, options.destination, options.encode_only)

if __name__ == '__main__':
    main()
