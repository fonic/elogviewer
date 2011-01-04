#!/usr/bin/env python

# vi:ts=4 st=4 sw=4 et
# (c) 2010 Mathias Laurin, GPL2
# see elogviewerCommon.py for details

import sys
from PyQt4 import QtCore, QtGui


from elogviewerCommon import FilterCommon, Elog, all_files
class Filter(FilterCommon):
    def __init__(self, label, match="", is_class=False, color='black'):
        self._button = QtGui.QCheckBox(label)
        self._button.setCheckState(True)
        FilterCommon.__init__(self, label, match, is_class, color)

    def is_active(self):
        return self._button.checkState() != 0

    def button(self):
        return self._button

from elogviewerQt_ui import Ui_MainWindow
from elogviewerCommon import ElogviewerIdentity, ElogviewerCommon
class elogviewerQt(QtGui.QMainWindow, ElogviewerCommon):
    def __init__(self, cmdline_args):
        QtGui.QMainWindow.__init__(self)
        ElogviewerCommon.__init__(self)
		self.cmdline_args = cmdline_args

    def create_gui(self):
        self.gui = Ui_MainWindow()
        self.gui.setupUi(self)
    
    def connect(self):
        pass

    def show(self):
        QtGui.QMainWindow.show(self)

    def refresh(self):
        pass

    def quit(self):
        pass

    def add_filter(self, filter):
        ElogviewerCommon.add_filter(self, filter)

        filter_class_box = self.gui.filter_class_layout
        filter_stage_box = self.gui.filter_stage_layout
        if filter.is_class():
            filter_class_box.addWidget(filter.button())
        else:
            filter_stage_box.addWidget(filter.button())
    
    def read_elog(self, elog): # self, selection
        html_elog_content = "<body>"
        selected_elog = elog
        for elog_section in selected_elog.contents(self.filter_list):
            html_elog_content = '%s <p style="color: %s">%s</p>' % (html_elog_content, 'red', elog_section)
        html_elog_content = '%s </body>' % (html_elog_content)
        document = QTextDocument()
        document.setHtml(html_elog_content)
        self.gui.textEdit.setDocument(document)


def main():
    app = QtGui.QApplication(sys.argv)
    elogviewer = elogviewerQt()
    elogviewer.create_gui()

    elogviewer.add_filter(Filter("info", "INFO", True, 'darkgreen'))
    elogviewer.add_filter(Filter("warning", "WARN", True, 'red'))
    elogviewer.add_filter(Filter("error", "ERROR", True, 'orange'))
    elogviewer.add_filter(Filter("log", "LOG", True))
    elogviewer.add_filter(Filter("QA", "QA", True))

    elogviewer.add_filter(Filter("preinst"))
    elogviewer.add_filter(Filter("postinst"))
    elogviewer.add_filter(Filter("prerm"))
    elogviewer.add_filter(Filter("postrm"))
    elogviewer.add_filter(Filter("unpack"))
    elogviewer.add_filter(Filter("compile"))
    elogviewer.add_filter(Filter("setup"))
    elogviewer.add_filter(Filter("test"))
    elogviewer.add_filter(Filter("install"))
    elogviewer.add_filter(Filter("prepare"))
    elogviewer.add_filter(Filter("configure"))
    elogviewer.add_filter(Filter("other"))

    elogviewer.connect()
    elogviewer.show()
    elogviewer.refresh()
    elogviewer.main()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

