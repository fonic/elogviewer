#!/usr/bin/env python

# vi:ts=4 st=4 sw=4 et
# (c) 2010 Mathias Laurin, GPL2
# see elogviewerCommon.py for details

import sys
from PyQt4 import QtCore, QtGui
import libelogviewer.core as ev


class ElogInstanceItem(QtGui.QStandardItem):
	def __init__(self, elog):
		QtGui.QStandardItem.__init__(self)
		self.elog = elog
	
	def type(self):
		return 1000


( CATEGORY, PACKAGE, TIMESTAMP, ELOG ) = range(4)
FILENAME = QtCore.Qt.UserRole
TIMESORT = QtCore.Qt.UserRole
class Model(QtGui.QStandardItemModel):
	def __init__(self, parent=None):
		QtGui.QStandardItemModel.__init__(self, parent)
		self.setColumnCount(4)
		self.setHeaderData( CATEGORY, QtCore.Qt.Horizontal, "Category" )
		self.setHeaderData( PACKAGE, QtCore.Qt.Horizontal, "Package" )
		self.setHeaderData( TIMESTAMP, QtCore.Qt.Horizontal, "Timestamp" )
		self.setHeaderData( ELOG, QtCore.Qt.Horizontal, "Elog" )
		
		# maintain separate list of elog
		self.elog_dict = {}
	
	def appendRow(self, elog):
		# maintain separate list of elogs
		self.elog_dict[elog.filename] = elog
		category_it = QtGui.QStandardItem(elog.category)
		package_it = QtGui.QStandardItem(elog.package)
		package_it.setData(QtCore.QVariant(elog.filename), FILENAME)
		time_it = QtGui.QStandardItem(elog.locale_time)
		time_it.setData(QtCore.QVariant(elog.sorted_time), TIMESORT)
		elog_it = ElogInstanceItem(elog)
		return QtGui.QStandardItemModel.appendRow(self, [
			category_it, package_it, time_it, elog_it ])
	

class Filter(ev.FilterCommon):
    def __init__(self, label, match="", is_class=False, color='black'):
        self.button = QtGui.QCheckBox(label)
        self.button.setCheckState(True)
        ev.FilterCommon.__init__(self, label, match, is_class, color)

    def is_active(self):
        return self.button.checkState() != 0


from libelogviewer.qt.elogviewer_ui import Ui_MainWindow
class ElogviewerQt(QtGui.QMainWindow, ev.ElogviewerCommon):
    def __init__(self, cmdline_args):
        QtGui.QMainWindow.__init__(self)
        ev.ElogviewerCommon.__init__(self)
		self.cmdline_args = cmdline_args
		self.model = Model()
		self.selected_elog = None

    def create_gui(self):
        self.gui = Ui_MainWindow()
        self.gui.setupUi(self)

		self.gui.treeView.setRootIsDecorated(False)
		self.gui.treeView.setModel(self.model)
		self.gui.treeView.setColumnHidden(ELOG, True)
	
    def connect(self):
		self.gui.treeView.connect(self.gui.treeView.selectionModel(),
				QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),
				self.selection_changed)
	
	def selection_changed(self, new_selection, old_selection):
		idx = new_selection.indexes()
		if idx[PACKAGE].isValid():
			filename = idx[PACKAGE].data(FILENAME).toString()
			self.selected_elog = self.model.elog_dict[str(filename)]
		else:
			self.selected_elog = None
		self.read_elog()
	
	def on_actionDelete_triggered(self, checked=None):
		if checked is None: return
		idx = self.gui.treeView.selectedIndexes()
		filename_selected = idx[PACKAGE].data(FILENAME).toString()
		print "Delete " + filename_selected

	def on_actionRefresh_triggered(self, checked=None):
		if checked is None: return
		self.refresh()

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
		for file in ev.all_files(self.cmdline_args.get_elogdir(), '*:*.log', False, True):
			self.model.appendRow(ev.Elog(file, self.cmdline_args.get_elogdir()))

    def add_filter(self, filter):
        ev.ElogviewerCommon.add_filter(self, filter)

        filter_class_box = self.gui.filter_class_layout
        filter_stage_box = self.gui.filter_stage_layout
        if filter.is_class():
            filter_class_box.addWidget(filter.button)
        else:
            filter_stage_box.addWidget(filter.button)
    
    def read_elog(self):
		if self.selected_elog is None:
			self.gui.textEdit.clear()
		html = []
        for elog_part in self.selected_elog.contents(self.filter_list):
			html.append('<p style="color: %s">%s</p>' % 
					(self.filter_list[elog_part.header].color, elog_part.content))
		html = ''.join(html)
		self.gui.textEdit.clear()
		self.gui.textEdit.append(html)

