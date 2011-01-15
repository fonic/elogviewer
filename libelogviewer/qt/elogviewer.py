#!/usr/bin/env python

# vi:ts=4 st=4 sw=4 et
# (c) 2010 Mathias Laurin, GPL2
# see elogviewerCommon.py for details

import sys
from PyQt4 import QtCore, QtGui
import libelogviewer.core as ev

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
	
	def append(self, elog):
		elog_it = QtGui.QStandardItem("elog")
		category_it = QtGui.QStandardItem(elog.category)
		package_it = QtGui.QStandardItem(elog.package)
		locale_time_it = QtGui.QStandardItem(elog.locale_time)
		sorted_time_it = QtGui.QStandardItem(elog.sorted_time)
		filename_it = QtGui.QStandardItem(elog.filename)
		return QtGui.QStandardItemModel.appendRow(self, [ elog_it,
			category_it, package_it, locale_time_it,
			sorted_time_it, filename_it])
	
	def getItem(self, row):
		return QtGui.QStandardItemModel.item(self, row, 0)


class Filter(ev.FilterCommon):
    def __init__(self, label, match="", is_class=False, color='black'):
        self.button = QtGui.QCheckBox(label)
        self.button.setCheckState(True)
        ev.FilterCommon.__init__(self, label, match, is_class, color)

    def is_active(self):
        return self._button.checkState() != 0


from libelogviewer.qt.elogviewer_ui import Ui_MainWindow
class ElogviewerQt(QtGui.QMainWindow, ev.ElogviewerCommon):
    def __init__(self, cmdline_args):
        QtGui.QMainWindow.__init__(self)
        ev.ElogviewerCommon.__init__(self)
		self.cmdline_args = cmdline_args
		self.model = Model()

    def create_gui(self):
        self.gui = Ui_MainWindow()
        self.gui.setupUi(self)

		self.gui.treeView.setRootIsDecorated(False)
		self.gui.treeView.setModel(self.model)
	
	def get_model(self):
		return self.gui.treeView.model()

    def connect(self):
		self.gui.treeView.connect(self.gui.treeView.selectionModel(),
				QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),
				self.selection_changed)
	
	def selection_changed(self, new_selection, old_selection):
		row = new_selection.indexes()[1].row()
	
	def on_actionQuit_triggered(self, checked=None):
		if checked is None: return
		self.quit()
	
	def on_actionDelete_triggered(self, checked=None):
		if checked is None: return
		print "actionDelete"

	def on_actionRefresh_triggered(self, checked=None):
		if checked is None: return
		self.clear()
		self.populate()

	def on_actionAbout_triggered(self, checked=None):
		if checked is None: return
		print "actionAbout"
	
    def show(self):
        QtGui.QMainWindow.show(self)

	def clear(self):
		pass

    def refresh(self):
		self.clear()
		self.populate()

	def populate(self):
		model = self.get_model()
		for file in ev.all_files(self.cmdline_args.get_elogdir(), '*:*.log', False, True):
			model.append(ev.Elog(file, self.cmdline_args.get_elogdir()))

    def quit(self):
		print "quit"

    def add_filter(self, filter):
        ev.ElogviewerCommon.add_filter(self, filter)

        filter_class_box = self.gui.filter_class_layout
        filter_stage_box = self.gui.filter_stage_layout
        if filter.is_class():
            filter_class_box.addWidget(filter.button)
        else:
            filter_stage_box.addWidget(filter.button)
    
    def read_elog(self, elog): # self, selection
        html_elog_content = "<body>"
        selected_elog = elog
        for elog_section in selected_elog.contents(self.filter_list):
            html_elog_content = '%s <p style="color: %s">%s</p>' % (html_elog_content, 'red', elog_section)
        html_elog_content = '%s </body>' % (html_elog_content)
        document = QTextDocument()
        document.setHtml(html_elog_content)
        self.gui.textEdit.setDocument(document)
