#!/usr/bin/env python

# vi:ts=4 st=4 sw=4 et
# (c) 2010 Mathias Laurin, GPL2
# see elogviewerCommon.py for details

import sys
from PyQt4 import QtCore, QtGui

from elogviewerQt_ui import Ui_MainWindow

class elogviewerQt(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

def main():
    app = QtGui.QApplication(sys.argv)
    gui = elogviewerQt()
    gui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

