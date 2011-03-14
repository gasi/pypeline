#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
parser.py

Created by Daniel Gasienica on 2010-12-29.
Copyright (c) 2010 Daniel Gasienica. All rights reserved.
"""

import datetime
import os
import re

ILLEGAL_CHARACTERS = ['.', '_', '-', ':', '{', '}', '[', ']', '(', ')']
SEPARATOR = ' '
MIN_YEAR = 1888 # http://en.wikipedia.org/wiki/Roundhay_Garden_Scene

def parse_tv_show(path):
    normalized_filename = get_normalized_filename(path)
    match = re.search(r'(.*)s(\d+)e(\d+).*', normalized_filename)
    if match is None:
        return None
    tv_show = {'series_title': match.group(1).strip(),
               'season': int(match.group(2)),
               'episode': int(match.group(3))}
    return tv_show

def parse_movie(path):
    title = get_normalized_filename(path)
    year_strings = re.findall(r'(\d{4})', title)
    year = None
    for year_string in reversed(year_strings):
        year_index = title.rindex(year_string)
        if is_valid_year(int(year_string)) and year_index > 0:
            title = title[:year_index]
            year = int(year_string)
            break
    movie = {'title': title.strip()}
    if year:
        movie['year'] = year
    return movie

def is_valid_year(year):
    return MIN_YEAR <= year <= datetime.datetime.now().year + 1

def get_normalized_filename(path):
    filename, _ = os.path.splitext(os.path.basename(path))
    for char in ILLEGAL_CHARACTERS:
        filename = filename.replace(char, SEPARATOR)
    filename = ' '.join(filename.split())
    return filename.lower().strip()
