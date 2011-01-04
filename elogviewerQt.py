#!/usr/bin/env python

# vi:ts=4 st=4 sw=4 et
# (c) 2010 Mathias Laurin, GPL2
# see elogviewerCommon.py for details

import sys
from PyQt4 import QtCore, QtGui

( ELOG, CATEGORY, PACKAGE, TIMESTAMP, TIMESORT, FILENAME ) = range(6)
class Model(QtGui.QStandardItemModel):
	def __init__(self):
		QtGui.QStandardItemModel.__init__(self)
		self.setColumnCount(6)
		self.setHeaderData( ELOG, QtCore.Qt.Horizontal, "Elog" )
		self.setHeaderData( CATEGORY, QtCore.Qt.Horizontal, "Category" )
		self.setHeaderData( PACKAGE, QtCore.Qt.Horizontal, "Package" )
		self.setHeaderData( TIMESTAMP, QtCore.Qt.Horizontal, "Timestamp" )
		self.setHeaderData( TIMESORT, QtCore.Qt.Horizontal, "Time sort order" )
		self.setHeaderData( FILENAME, QtCore.Qt.Horizontal, "Filename" )
	
	def appendRow(self, elog):
		return QtGui.QStandardItemModel.appendRow(self, [ elog,
			elog.category(), elog.package(), elog.locale_time(),
			elog.sorted_time(), elog.filename()])
	
	def getItem(self, row):
		return QtGui.QStandardItemModel.item(row, 0)

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
class ElogviewerQt(QtGui.QMainWindow, ElogviewerCommon):
    def __init__(self, cmdline_args):
        QtGui.QMainWindow.__init__(self)
        ElogviewerCommon.__init__(self)
		self.cmdline_args = cmdline_args

    def create_gui(self):
        self.gui = Ui_MainWindow()
        self.gui.setupUi(self)

		model = Model()

		self.gui.treeView.setModel(model)
		self.gui.treeView.setRootIsDecorated(False)

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

