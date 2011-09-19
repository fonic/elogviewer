"""
Usage:
    python setup.py
"""

from distutils.core import setup

setup(name="elogviewer",
      version="1.0.1",
      author="Mathias Laurin",
      author_email="Mathias.Laurin+gentoo.org@gmail.com",
      url="http://sourceforge.net/projects/elogviewer/",
      license="GPL2",
      packages=["libelogviewer", "libelogviewer/ev_gtk", "libelogviewer/ev_qt"],
      package_data={"libelogviewer": ["libelogviewer/rsc/qt.qrc"],
                    "libelogviewer/ev_gtk": ["libelogviewer/ev_gtk/elogviewer.glade"]
                    },
	  #data_files=[('libelogviewer/ev_gtk', ['libelogviewer/ev_gtk/elogviewer.glade']),],
      scripts=["elogviewer.py"],
     )
