#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
pypeline

Created by Daniel Gasienica on 2010-12-29.
Copyright (c) 2010 Daniel Gasienica. All rights reserved.
"""

VERSION = "0.1"
VERSION_INFO = (0, 1, 0)

import imdb
import glob
import logging
import os
import os.path
import parser
import re
import subprocess

SOURCE = '~/Downloads'
TARGET = '~/Movies'
ENCODED_EXTENSIONS = ['m4v']
EXTENSIONS = ['wmv', 'avi', 'mpg', 'mpeg', 'mkv'] + ENCODED_EXTENSIONS
SERIES_OVERRIDES = {}
MOVIE_OVERRIDES = {}

IMDb = imdb.IMDb()

ILLEGAL_CHARACTERS = ['[', ']', '*']
HANDBRAKE = '../vendor/handbrake/HandbrakeCLI'
ATOMIC_PARSLEY = '../vendor/atomic_parsley/AtomicParsley'

# Apple TV settings
def encode(source, target):
    with open(os.devnull, 'w') as nirvana:
        subprocess.call([HANDBRAKE,
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
                         '-X', '960',
                         '--loose-anamorphic', '',
                         '-m', '',
                         '-x', 'cabac=0:ref=2:me=umh:b-adapt=2:weightb=0:trellis=0:weightp=0'],
                         stdout=nirvana, stderr=nirvana)

def get_imdb_descriptor(item):
    descriptor = None
    if 'series_title' in item:
        series_title = item['series_title'].lower()
        if series_title not in SERIES_OVERRIDES:
            movie = IMDb.search_movie(series_title)[0]
        else:
            movie = IMDb.get_movie(SERIES_OVERRIDES[series_title])
        IMDb.update(movie, 'episodes')
        episode = movie['episodes'][item['season']][item['episode']]
        descriptor = {'series_title': episode['series title'],
                      'title': str(episode['title']),
                      'season': int(episode['season']),
                      'episode': int(episode['episode']),
                      'year': int(episode['year']),
                      'plot': episode.get('plot', '')}
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
                      'year': int(movie['year'])}
    return descriptor

def set_metadata(filename, descriptor):
    args = [ATOMIC_PARSLEY,
            filename,
            '--title', '%(title)s' % descriptor,
            '--year', '%(year)d' % descriptor,
            '--description', '%(plot)s' % descriptor]
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
    temp_filename = get_target_temp_filename(filename)
    if temp_filename:
        os.remove(filename)
        os.rename(temp_filename, filename)

def get_target_temp_filename(filename):
    root, ext = os.path.splitext(filename)
    files = glob.glob(root + '-temp-*.m4v')
    temp_filename = files[0] if files else None
    return temp_filename

def get_target_filename(filename, descriptor):
    target_basename = os.path.basename(os.path.splitext(filename)[0])
    if descriptor:
        if 'series_title' in descriptor:
            target_basename = '%(series_title)s S%(season)02dE%(episode)02d' % descriptor
        elif 'title' in descriptor:
            target_basename = '%(title)s' % descriptor
    for char in ILLEGAL_CHARACTERS:
        target_basename = target_basename.replace(char, '')
    target = os.path.join(TARGET, target_basename + '.m4v')
    return target

def get_sources(path):
    sources = []
    for extension in EXTENSIONS:
        sources += glob.glob(path + '/*.' + extension)
        sources += glob.glob(path + '/**/*.' + extension)
    return sorted(sources)

def main():
    sources = get_sources(SOURCE)
    for source in sources:
        # acquire metadata
        item = parser.parse_tv_show(source)
        if not item:
            item = parser.parse_movie(source)
        descriptor = None
        if item:
            descriptor = get_imdb_descriptor(item)

        # encoding
        target = get_target_filename(source, descriptor)
        if not os.path.exists(target):
            encode(source, target)

        # metadata
        if descriptor:
            set_metadata(target, descriptor)

if __name__ == '__main__':
    main()
