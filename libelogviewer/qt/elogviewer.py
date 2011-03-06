#!/usr/bin/env python

# vi:ts=4 st=4 sw=4 et
# (c) 2010 Mathias Laurin, GPL2
# see elogviewerCommon.py for details

import sys
from PyQt4 import QtCore, QtGui
import libelogviewer.core as core


class ElogInstanceItem(QtGui.QStandardItem):
    def __init__(self, elog):
        QtGui.QStandardItem.__init__(self)
        self.elog = elog
    
    def type(self):
        return 1000


( CATEGORY, PACKAGE, TIMESTAMP, ELOG ) = range(4)
SORT = QtCore.Qt.UserRole
FILENAME = QtCore.Qt.UserRole + 1
class Model(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, parent)
        self.setColumnCount(4)
        self.setHeaderData( CATEGORY, QtCore.Qt.Horizontal, "Category" )
        self.setHeaderData( PACKAGE, QtCore.Qt.Horizontal, "Package" )
        self.setHeaderData( TIMESTAMP, QtCore.Qt.Horizontal, "Timestamp" )
        self.setHeaderData( ELOG, QtCore.Qt.Horizontal, "Elog" )
        self.setSortRole(SORT)

        # maintain separate list of elog
        self.elog_dict = {}
    
    def EVappend(self, elog):
        self.appendRow(elog)
    
    def appendRow(self, elog):
        self.elog_dict[elog.filename] = elog
        
        category_it = QtGui.QStandardItem(elog.category)
        category_it.setData(QtCore.QVariant(elog.category), SORT)
        
        package_it = QtGui.QStandardItem(elog.package)
        package_it.setData(QtCore.QVariant(elog.package), SORT)
        package_it.setData(QtCore.QVariant(elog.filename), FILENAME)

        time_it = QtGui.QStandardItem(elog.locale_time)
        time_it.setData(QtCore.QVariant(elog.sorted_time), SORT)
        
        elog_it = ElogInstanceItem(elog)
        return QtGui.QStandardItemModel.appendRow(self, [
            category_it, package_it, time_it, elog_it ])
    
    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        for current_row in xrange(row, row+count):
            idx = self.index(current_row, PACKAGE, parent)
            filename = str(idx.data(FILENAME).toString())
            if filename in self.elog_dict:
                del self.elog_dict[filename]
        return QtGui.QStandardItemModel.removeRows(self, row, count, parent)
    

class Filter(core.Filter):
    def __init__(self, label, match="", is_class=False, color='black'):
        self.button = QtGui.QCheckBox(label)
        self.button.setCheckState(QtCore.Qt.Checked)
        core.Filter.__init__(self, label, match, is_class, color)

    def is_active(self):
        return self.button.checkState() != 0


from libelogviewer.qt.elogviewer_ui import Ui_MainWindow
class ElogviewerQt(QtGui.QMainWindow, core.Elogviewer):
    def __init__(self, cmdline_args):
        QtGui.QMainWindow.__init__(self)
        core.Elogviewer.__init__(self)
        self.cmdline_args = cmdline_args
        self.model = Model()
        self.selected_elog = None

    def create_gui(self):
        self.gui = Ui_MainWindow()
        self.gui.setupUi(self)

        self.gui.treeView.setRootIsDecorated(False)
        self.gui.treeView.setModel(self.model)
        self.gui.treeView.setColumnHidden(ELOG, True)

        header = self.gui.treeView.header()
        header.setSortIndicatorShown(True)
        header.setClickable(True)

        # see http://standards.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html#names
        # http://www.qtcentre.org/wiki/index.php?title=Embedded_resources
        # http://doc.trolltech.com/latest/qstyle.html#StandardPixmap-enum

        style = QtGui.QApplication.style()

        refreshicon = QtGui.QIcon.fromTheme("view-refresh", 
                style.standardIcon(QtGui.QStyle.SP_BrowserReload))
        self.gui.actionRefresh.setIcon(refreshicon)

        deleteicon = QtGui.QIcon.fromTheme("edit-delete",
                QtGui.QIcon(":/trolltech/styles/commonstyle/images/standardbutton-delete-32.png"))
        self.gui.actionDelete.setIcon(deleteicon)

    def connect(self):
        self.gui.treeView.connect(self.gui.treeView.selectionModel(),
                QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),
                self.on_selection_changed)
        self.gui.treeView.header().connect(self.gui.treeView.header(),
                QtCore.SIGNAL("sortIndicatorChanged(int, Qt::SortOrder)"),
                self.model.sort)
    
    def on_selection_changed(self, new_selection, old_selection):
        idx = new_selection.indexes()
        if len(idx) is not 0:
            idx = idx[PACKAGE]
            row = idx.row() + 1
            filename = str(idx.data(FILENAME).toString())
            self.selected_elog = self.model.elog_dict[filename]
        else:
            self.selected_elog = None
            row = 0
        self.update_statusbar(row)
        self.read_elog()
    
    def on_actionDelete_triggered(self, checked=None):
        if checked is None: return
        idx = self.gui.treeView.selectedIndexes()
        if len(idx) is not 0:
            filename = self.model.index(idx[0].row(), PACKAGE).data(FILENAME).toString()
            filename = str(filename)
            if self.cmdline_args.debug:
                print "%s deleted" % filename
            else:
                self.model.elog_dict[filename].delete()
            self.model.removeRow(idx[0].row())

    def on_actionRefresh_triggered(self, checked=None):
        if checked is None: return
        self.refresh()

    def show(self):
        QtGui.QMainWindow.show(self)
        self.populate()
        self.update_statusbar()
        self.read_elog()
    
    def refresh(self):
        self.model.removeRows(0, self.model.rowCount()) 
        self.populate()

    def add_filter(self, filter):
        filter.button.connect(filter.button, QtCore.SIGNAL("stateChanged(int)"),
                self.read_elog)
        (t, l) = core.Elogviewer.add_filter(self, filter)

        filter_table = self.gui.filter_class_layout if filter.is_class() \
                else self.gui.filter_stage_layout
        filter_table.addWidget(filter.button, t, l)
    
    def read_elog(self):
        self.gui.textEdit.clear()
        self.gui.textEdit.append( '''
<h1>(k)elogviewer 1.0.0</h1>
<center><small>(k)elogviewer, copyright (c) 2007, 2011 Mathias Laurin<br>
kelogviewer, copyright (c) 2007 Jeremy Wickersheimer<br>
GNU General Public License (GPL) version 2</small><br>
<a href=http://sourceforge.net/projects/elogviewer>http://sourceforge.net/projects/elogviewer</a></center>
<h2>Written by</h2>
Mathias Laurin <a href="mailto:mathias_laurin@users.sourceforge.net?Subject=elogviewer">
&lt;mathias_laurin@users.sourceforge.net&gt;</a><br>
Timothy Kilbourn (initial author)<br>
Jeremy Wickersheimer (qt3/KDE port)
<h2>With contributions from</h2>
Radice David, gentoo bug #187595<br>
Christian Faulhammer, gentoo bug #192701
<h2>Documented by</h2>
Christian Faulhammer <a href="mailto:opfer@gentoo.org">&lt;opfer@gentoo.org&gt;</a>
<h2>Artwork by</h2>
'''         if self.selected_elog is None else ''.join( '<p style="color: %s">%s</p>' % 
                    (self.filter_list[elog_part.header].color, elog_part.content)
                    for elog_part in self.selected_elog.contents(self.filter_list) ))
    
    def update_statusbar(self, idx=0):
        self.gui.statusbar.showMessage(self.message_statusbar(idx, self.model.rowCount()))

