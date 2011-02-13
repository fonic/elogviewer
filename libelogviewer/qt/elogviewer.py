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
		self.elog_dict[elog.filename] = elog
		category_it = QtGui.QStandardItem(elog.category)
		package_it = QtGui.QStandardItem(elog.package)
		package_it.setData(QtCore.QVariant(elog.filename), FILENAME)
		time_it = QtGui.QStandardItem(elog.locale_time)
		time_it.setData(QtCore.QVariant(elog.sorted_time), TIMESORT)
		elog_it = ElogInstanceItem(elog)
		return QtGui.QStandardItemModel.appendRow(self, [
			category_it, package_it, time_it, elog_it ])
	
	def removeRows(self, row, count, parent=QtCore.QModelIndex()):
		for current_row in xrange(row, row+count):
			idx = self.index(current_row, PACKAGE, parent)
			filename = str(idx.data(FILENAME).toString())
			print filename
			if filename in self.elog_dict:
				# self.elog_dict[FILENAME].delete()
				del self.elog_dict[filename]
		return QtGui.QStandardItemModel.removeRows(self, row, count, parent)
	

class Filter(ev.FilterCommon):
    def __init__(self, label, match="", is_class=False, color='black'):
        self.button = QtGui.QCheckBox(label)
        self.button.setCheckState(QtCore.Qt.Checked)
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

		self.class_counter = self.stage_counter = 0
		self.class_columns = self.stage_columns = 2

    def create_gui(self):
        self.gui = Ui_MainWindow()
        self.gui.setupUi(self)

		self.gui.treeView.setRootIsDecorated(False)
		self.gui.treeView.setModel(self.model)
		self.gui.treeView.setColumnHidden(ELOG, True)

		refreshicon = QtGui.QIcon(QtGui.QPixmap("refresh.png"))
		self.gui.actionRefresh.setIcon(refreshicon)

		deleteicon = QtGui.QIcon(QtGui.QPixmap("delete.png"))
		self.gui.actionDelete.setIcon(deleteicon)

		abouticon = QtGui.QIcon(QtGui.QPixmap("about.png"))
		self.gui.actionAbout.setIcon(abouticon)
		self.gui.actionAbout.setMenuRole(QtGui.QAction.AboutRole)

		quiticon = QtGui.QIcon(QtGui.QPixmap("quit.png"))
		self.gui.actionQuit.setIcon(quiticon)
		self.gui.actionQuit.setIconVisibleInMenu(True)
		self.gui.actionQuit.setMenuRole(QtGui.QAction.QuitRole)

		self.update_statusbar()

	
    def connect(self):
		self.gui.treeView.connect(self.gui.treeView.selectionModel(),
				QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),
				self.selection_changed)
	
	def selection_changed(self, new_selection, old_selection):
		idx = new_selection.indexes()
		if len(idx) is not 0:
			idx = idx[PACKAGE]
			filename = str(idx.data(FILENAME).toString())
			self.selected_elog = self.model.elog_dict[filename]
		else:
			self.selected_elog = None
		self.update_statusbar(idx.row() + 1)
		self.read_elog()
	
	def on_actionDelete_triggered(self, checked=None):
		if checked is None: return
		idx = self.gui.treeView.selectedIndexes()
		if len(idx) is not 0:
			self.model.removeRow(idx[0].row())

	def on_actionRefresh_triggered(self, checked=None):
		if checked is None: return
		self.refresh()

	def on_actionAbout_triggered(self, checked=None):
		if checked is None: return
		print "actionAbout"
	
    def show(self):
        QtGui.QMainWindow.show(self)
	
    def refresh(self):
		self.model.removeRows(0, self.model.rowCount()) 
		self.populate()

	def populate(self):
		for file in ev.all_files(self.cmdline_args.get_elogdir(), '*:*.log', False, True):
			self.model.appendRow(ev.Elog(file, self.cmdline_args.get_elogdir()))

	def add_filter(self, filter):
		filter.button.connect(filter.button, QtCore.SIGNAL("stateChanged(int)"),
				self.read_elog)
        ev.ElogviewerCommon.add_filter(self, filter)

        filter_class_box = self.gui.filter_class_layout
        filter_stage_box = self.gui.filter_stage_layout
        if filter.is_class():
			(t, l) = divmod(self.class_counter, self.class_columns)
            filter_class_box.addWidget(filter.button, t, l)
			self.class_counter += 1
        else:
			(t, l) = divmod(self.stage_counter, self.stage_columns)
            filter_stage_box.addWidget(filter.button, t, l)
			self.stage_counter += 1
    
    def read_elog(self):
		if self.selected_elog is None:
			self.gui.textEdit.clear()
			return
		html = []
        for elog_part in self.selected_elog.contents(self.filter_list):
			html.append('<p style="color: %s">%s</p>' % 
					(self.filter_list[elog_part.header].color, elog_part.content))
		html = ''.join(html)
		self.gui.textEdit.clear()
		self.gui.textEdit.append(html)
	
	def update_statusbar(self, idx=0):
		if self.selected_elog is None:
			filename = "no selection"
		else:
			filename = self.selected_elog.package
		model_size = self.model.rowCount()
		message = "%i of %i\t%s" % (idx, model_size, filename)
		self.gui.statusbar.showMessage(message)

