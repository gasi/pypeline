#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages
import pypeline

setup(name='pypeline',
      version=pypeline.VERSION,
      description='pypeline encodes and tags your movies & TV shows for iTunes',
      author='Daniel Gasienica',
      author_email='daniel@gasienica.ch',
      keywords='pypeline itunes m4v tags movies tvshows tv encoding handbrake',
      url='https://github.com/gasi/pypeline',
      packages = ['pypeline', 'vendor'],
      include_package_data=True,
      entry_points = {
        'console_scripts': [
            'pypeline = pypeline:main'
        ]
      })
