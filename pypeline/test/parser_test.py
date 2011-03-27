#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
parse_movie_test.py

Created by Daniel Gasienica on 2010-12-29.
Copyright (c) 2010 Daniel Gasienica. All rights reserved.
"""

import pypeline
import unittest

class TestParser(unittest.TestCase):
    MOVIES = [('Control[2007]DvDrip[Eng]-FXG.avi',
               {'title': 'control', 'year': 2007}),
              ('Prozac Nation (2001) [DvdRip] [Xvid] {1337x}-Noir.avi',
               {'title': 'prozac nation', 'year': 2001}),
              ('Rabbit.Hole.2010.DVDSCREENER.XviD-FRAGMENT.avi',
               {'title': 'rabbit hole', 'year': 2010}),
              ('sample.avi',
               {'title': 'sample'}),
              ('Die.Hard.2-Die.Harder[1990]DvDrip-aXXo.mkv',
               {'title': 'die hard 2 die harder', 'year': 1990}),
              ('Die.Hard-With.A.Vengeance[1995]DvDrip-aXXo.avi',
               {'title': 'die hard with a vengeance', 'year': 1995}),
              ('2001.A.Space.Odyssey[1968].wmv',
               {'title': '2001 a space odyssey', 'year': 1968})]

    TV_SHOWS = [('Glee.S02E15.HDTV.XviD-LOL.[VTV].avi',
                {'series_title': 'glee', 'season': 2, 'episode': 15}),
                ('30 Rock S04 E01 - Season 4.avi',
                {'series_title': '30 rock', 'season': 4, 'episode': 1})]

    def test_parse_movie(self):
        for filename, movie in self.MOVIES:
            self.assertEqual(pypeline.parser.parse_movie(filename), movie)

    def test_parse_tv_show(self):
        for filename, tv_show in self.TV_SHOWS:
            self.assertEqual(pypeline.parser.parse_tv_show(filename), tv_show)

if __name__ == '__main__':
    unittest.main()
