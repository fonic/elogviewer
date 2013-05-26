#!/usr/bin/env python
# (c) 2011, 2013 Mathias Laurin, GPL2
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# Street, Fifth Floor, Boston, MA  02110-1301, USA.

import sys
import os
import argparse
import fnmatch
import time
import re
from functools import partial

import sip as _sip
_sip.setapi("QVariant", 2)
_sip.setapi("QString", 2)


from PyQt4 import QtCore, QtGui
Qt = QtCore.Qt

try:
    import portage
except ImportError:
    portage = None


CATEGORY, PACKAGE, ECLASS, TIMESTAMP, ELOG = range(5)
SORT = QtCore.Qt.UserRole
FILENAME = QtCore.Qt.UserRole + 1


def all_files(root, patterns='*', single_level=False, yield_folders=False):
    ''' Expand patterns for semicolon-separated strin of list '''
    patterns = patterns.split(';')
    for path, subdirs, files in os.walk(root):
        if yield_folders:
            files.extend(subdirs)
        files.sort()
        for name in files:
            for pattern in patterns:
                if fnmatch.fnmatch(name, pattern):
                    yield os.path.join(path, name)
                    break
        if single_level:
            break


class Role(object):

    Category = Qt.UserRole + 1
    EClass = Qt.UserRole + 2
    Filename = Qt.UserRole + 3
    Package = Qt.UserRole + 4
    Date = Qt.UserRole + 5


class Elog(object):

    def __init__(self, filename):
        self.filename = filename
        basename = os.path.basename(filename)
        try:
            self.category, self.package, rest = basename.split(":")
        except ValueError:
            self.category = os.path.dirname(filename).split(os.sep)[-1]
            self.package, rest = basename.split(":")
        date, ext = os.path.splitext(rest)
        self.date = time.strptime(date, "%Y%m%d-%H%M%S")

        # Get the highest elog class. Adapted from Luca Marturana's elogv.
        eClasses = re.findall("LOG:|INFO:|WARN:|ERROR:", self.text)
        if "ERROR:" in eClasses:
            self.eclass = "eerror"
        elif "WARN:" in eClasses:
            self.eclass = "ewarn"
        elif "LOG:" in eClasses:
            self.eclass = "elog"
        else:
            self.eclass = "einfo"

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.filename)

    def delete(self):
        os.remove(self.filename)  # XXX

    @property
    def text(self):
        if self.filename:
            with open(self.filename, "r") as elogfile:
                return elogfile.read()

    @property
    def isoTime(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", self.date)

    @property
    def localeTime(self):
        return time.strftime("%x %X", self.date)


class ModelItem(QtGui.QStandardItem):

    def __init__(self, elog=None):
        super(ModelItem, self).__init__()
        self.__elog = elog

    def type(self):
        return self.UserType + 1

    def clone(self):
        return self.__class__()

    def data(self, role=Qt.UserRole + 1):
        if self.__elog and role in (Qt.DisplayRole, Qt.EditRole):
            try:
                return {CATEGORY: self.__elog.category,
                        PACKAGE: self.__elog.package,
                        ECLASS: self.__elog.eclass,
                        TIMESTAMP: self.__elog.localeTime,
                        ELOG: self.__elog.text}.get(self.column(), ELOG)
            except KeyError:
                return super(ModelItem, self).data(role)
        else:
            return super(ModelItem, self).data(role)


class Model(QtGui.QStandardItemModel):

    def __init__(self, parent=None):
        super(Model, self).__init__(parent)
        self.setItemPrototype(ModelItem())

        self.setColumnCount(5)
        self.setHeaderData(CATEGORY, QtCore.Qt.Horizontal, "Category")
        self.setHeaderData(PACKAGE, QtCore.Qt.Horizontal, "Package")
        self.setHeaderData(ECLASS, QtCore.Qt.Horizontal, "Highest eclass")
        self.setHeaderData(TIMESTAMP, QtCore.Qt.Horizontal, "Timestamp")
        self.setHeaderData(ELOG, QtCore.Qt.Horizontal, "Elog")
        self.setSortRole(SORT)

    def populate(self, path):
        for nRow, filename in enumerate(
                all_files(path, "*:*.log", False, True)):
            elog = Elog(filename)
            self.invisibleRootItem().appendRow([
                ModelItem(elog) for column in range(self.columnCount())])


class Elogviewer(QtGui.QMainWindow):

    def __init__(self, args):
        super(Elogviewer, self).__init__()
        self._args = args

        self.display_elog = None
        self.selected_elog = None

        self.filter_list = {}
        self.filter_counter_class = self.filter_counter_stage = 0
        self.filter_columns_class = self.filter_columns_stage = 2

        self.__initUI()
        self.__initToolBar()

        self._tableView.model().populate(self._args.elogpath)

    def __initUI(self):
        self._centralWidget = QtGui.QWidget(self)
        centralLayout = QtGui.QVBoxLayout()
        self._centralWidget.setLayout(centralLayout)
        self.setCentralWidget(self._centralWidget)

        self._tableView = QtGui.QTableView(self._centralWidget)
        self._tableView.setSelectionMode(self._tableView.ExtendedSelection)
        centralLayout.addWidget(self._tableView)

        self._model = Model()
        self._tableView.setModel(self._model)
        self._tableView.setColumnHidden(ELOG, True)

        horizontalHeader = self._tableView.horizontalHeader()
        horizontalHeader.setSortIndicatorShown(True)
        horizontalHeader.setClickable(True)
        horizontalHeader.sortIndicatorChanged.connect(self._model.sort)

        bottomLayout = QtGui.QHBoxLayout()
        centralLayout.addLayout(bottomLayout)

        self._textEdit = QtGui.QTextEdit(self._centralWidget)
        self._textEdit.setReadOnly(True)
        self._textEdit.setHtml("""<h1>hello world</h1>""")
        bottomLayout.addWidget(self._textEdit)

        self._textWidgetMapper = QtGui.QDataWidgetMapper(self._tableView)
        self._textWidgetMapper.setSubmitPolicy(
            self._textWidgetMapper.AutoSubmit)
        self._textWidgetMapper.setModel(self._model)
        self._textWidgetMapper.addMapping(self._textEdit, ELOG)
        self._textWidgetMapper.toFirst()
        self._tableView.selectionModel().currentRowChanged.connect(
            self._textWidgetMapper.setCurrentModelIndex)

        filterLayout = QtGui.QVBoxLayout()
        bottomLayout.addLayout(filterLayout)

        self._filterClassBox = QtGui.QGroupBox("Elog class",
                                               self._centralWidget)
        filterLayout.addWidget(self._filterClassBox)

        self._filterStageBox = QtGui.QGroupBox("Elog stage",
                                               self._centralWidget)
        filterLayout.addWidget(self._filterStageBox)

    def __initToolBar(self):
        # see http://standards.freedesktop.org/icon-naming-spec/
        #   icon-naming-spec-latest.html#names
        # http://www.qtcentre.org/wiki/index.php?title=Embedded_resources
        # http://doc.trolltech.com/latest/qstyle.html#StandardPixmap-enum

        self._toolBar = QtGui.QToolBar(self)
        self.addToolBar(self._toolBar)

        style = QtGui.QApplication.style()

        self._refreshAction = QtGui.QAction("Refresh", self._toolBar)
        self._refreshAction.setIcon(QtGui.QIcon.fromTheme(
            "view-refresh", style.standardIcon(QtGui.QStyle.SP_BrowserReload)))
        self._refreshAction.triggered.connect(self.refresh)
        self._toolBar.addAction(self._refreshAction)

        self._deleteAction = QtGui.QAction("Delete", self._toolBar)
        self._deleteAction.setIcon(QtGui.QIcon.fromTheme(
            "edit-delete",
            QtGui.QIcon(":/trolltech/styles/commonstyle/images/standardbutton-delete-32.png")))
        self._toolBar.addAction(self._deleteAction)

        self._aboutAction = QtGui.QAction("About", self._toolBar)
        self._aboutAction.triggered.connect(partial(
            QtGui.QMessageBox.about,
            self, "About (k)elogviewer", " ".join((
                """
                <h1>(k)elogviewer 1.0.0</h1>
                <center><small>(k)elogviewer, copyright (c) 2007, 2011, 2013
                Mathias Laurin<br>
                kelogviewer, copyright (c) 2007 Jeremy Wickersheimer<br>
                GNU General Public License (GPL) version 2</small><br>
                <a href=http://sourceforge.net/projects/elogviewer>
                http://sourceforge.net/projects/elogviewer</a>
                </center>

                <h2>Written by</h2>
                Mathias Laurin <a href="mailto:mathias_laurin@users.sourceforge.net?Subject=elogviewer">
                &lt;mathias_laurin@users.sourceforge.net&gt;</a><br>
                Timothy Kilbourn (initial author)<br> 
                Jeremy Wickersheimer (qt3/KDE port)
                
                <h2>With contributions from</h2>
                Radice David, gentoo bug #187595<br>
                Christian Faulhammer, gentoo bug #192701

                <h2>Documented by</h2>
                Christian Faulhammer
                <a href="mailto:opfer@gentoo.org">&lt;opfer@gentoo.org&gt;</a>

                <h2>Artwork by</h2>
                (k)elogviewer application icon (c) gnome, GPL2

                """).splitlines())))
        self._toolBar.addAction(self._aboutAction)

        self._quitAction = QtGui.QAction("Quit", self._toolBar)
        self._toolBar.addAction(self._quitAction)

    def refresh(self):
        self._model.removeRows(0, self._model.rowCount())
        self._model.populate(self._args.elogpath)


def main():
    parser = argparse.ArgumentParser(description=os.linesep.join(
        """
        Elogviewer should help you not to miss important information.

        You need to enable the elog feature by setting at least one of
        PORTAGE_ELOG_CLASSES="info warn error log qa" and
        PORTAGE_ELOG_SYSTEM="save" in /etc/make.conf.

        You need to add yourself to the portage group to use elogviewer without
        privileges.

        Read /etc/make.conf.example for more information.

        """.splitlines()))
    parser.add_argument("-p", "--elogpath", help="path to the elog directory")
    parser.add_argument("-q", "--qt", action="store_true",
                        help="start with the Qt interface")
    args = parser.parse_args()

    app = QtGui.QApplication(sys.argv)

    elogviewer = Elogviewer(args)
    elogviewer.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
