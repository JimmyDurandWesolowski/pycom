#!/usr/bin/env python

from setuptools import setup

setup(name='pycom',
      version='0.1',
      # list folders, not files
      packages=[
          'pycom',
      ],
      scripts=[
          'bin/terminal',
      ],
      install_requires=[
          "pyserial >= 3.5",
      ],
      package_data={
          'pycom': ['conf/example.json']
      }
)
