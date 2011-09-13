"""
Usage:
    python setup.py
"""

from distutils.core import setup
from glob import glob

setup(name="elogviewer",
      version="1.0.0",
      author="Mathias Laurin",
      author_email="Mathias.Laurin+gentoo.org@gmail.com",
      url="http://sourceforge.net/projects/elogviewer/",
      license="GPL2",
      package_dir={"": "libelogviewer"},
      py_modules=["ev_gtk", "ev_qt"],
      #packages=[""],
      package_data={"": ["rsc/qt.rsc"]},
      scripts=["../elogviewer", "../kelogviewer"],
     )
