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
      #py_module=["libelogviewer"],
      #packages_dir={"": "libelogviewer"},
      packages=["libelogviewer", "libelogviewer/ev_gtk", "libelogviewer/ev_qt"],
      package_data={"": ["libelogviewer/rsc/qt.rsc"]}
     )
