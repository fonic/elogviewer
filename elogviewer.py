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
import locale
import time
import re
from functools import partial
from contextlib import closing

try:
    from StringIO import StringIO  # py2.7
except ImportError:
    from io import StringIO # py3+

import gzip
import bz2
try:
    import liblzma as lzma
except ImportError:
    lzma = None

try:
    from PySide import QtCore, QtGui
except ImportError:
    import sip as _sip
    for _type in "QDate QDateTime QString QVariant".split():
        _sip.setapi(_type, 2)
    from PyQt4 import QtCore, QtGui

Qt = QtCore.Qt

try:
    import portage
except ImportError:
    portage = None


__version__ = "2.1"


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

def _to_string(text):
    """This helper changes `bytes` to `str` on python3 and does nothing under
    python2."""
    try:
        return text.decode(locale.getpreferredencoding())
    except AttributeError:
        return text


class Role(object):

    SortRole = Qt.UserRole + 1


class Column(object):

    Category = 0
    Package = 1
    Flag = 2
    Eclass = 3
    Date = 4


class Elog(object):

    readflag = set()

    def __init__(self, filename):
        self.filename = filename
        basename = os.path.basename(filename)
        try:
            self.category, self.package, rest = basename.split(":")
        except ValueError:
            self.category = os.path.dirname(filename).split(os.sep)[-1]
            self.package, rest = basename.split(":")
        date = rest.split(".")[0]
        self.date = time.strptime(date, "%Y%m%d-%H%M%S")

        # Get the highest elog class. Adapted from Luca Marturana's elogv.
        with self.file as elogfile:
            eClasses = re.findall("LOG:|INFO:|WARN:|ERROR:",
                                  _to_string(elogfile.read()))
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
        os.remove(self.filename)
        Elog.readflag.remove(self.filename)

    @property
    def file(self):
        root, ext = os.path.splitext(self.filename)
        try:
            return {".gz": gzip.open,
                    ".bz2": bz2.BZ2File,
                    ".log": open}[ext](self.filename, "rb")
        except KeyError:
            return closing(StringIO(
                """
                <!-- set eclass: ERROR: -->
                <h2>Unsupported format</h2>
                The selected elog is in an unsupported format.
                """
            ))

    @property
    def htmltext(self):
        htmltext = []
        with self.file as elogfile:
            for line in elogfile:
                line = line.strip()
                if line.startswith("ERROR:"):
                    prefix = '<p style="color: orange">'
                elif line.startswith("WARN:"):
                    prefix = '<p style="color: red">'
                elif line.startswith("INFO:"):
                    prefix = '<p style="color: darkgreen">'
                elif (line.startswith("LOG:") or
                        line.startswith("QA:")):
                    prefix = '<p style="color: black">'
                else:
                    prefix = ""
                line = "".join((prefix, line, "<BR>"))
                htmltext.append(line)
        return os.linesep.join(htmltext)

    @property
    def isoTime(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", self.date)

    @property
    def localeTime(self):
        return time.strftime("%x %X", self.date)


class TextToHtmlDelegate(QtGui.QItemDelegate):

    def __init__(self, parent=None):
        super(TextToHtmlDelegate, self).__init__(parent)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.parent())

    def setEditorData(self, editor, index):
        if not index.isValid():
            return
        if isinstance(editor, QtGui.QTextEdit):
            item = index.model().itemFromIndex(index)
            editor.setHtml(item.elog().htmltext)


class ModelItem(QtGui.QStandardItem):

    def __init__(self, elog=None):
        super(ModelItem, self).__init__()
        self.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.__elog = elog

    def type(self):
        return self.UserType + 1

    def clone(self):
        return self.__class__()

    def elog(self):
        return self.__elog

    def markRead(self, readFlag=True):
        if readFlag:
            Elog.readflag.add(self.__elog.filename)
        else:
            try:
                Elog.readflag.remove(self.__elog.filename)
            except KeyError:
                pass

        font = self.font()
        font.setBold(not readFlag)
        self.setFont(font)

    def data(self, role=Qt.UserRole + 1):
        if not self.__elog:
            return super(ModelItem, self).data(role)
        if role == Role.SortRole:
            if self.column() == Column.Date:
                return self.__elog.isoTime
            else:
                return self.text()
        else:
            return super(ModelItem, self).data(role)


def populate(model, path):
    for nRow, filename in enumerate(
            all_files(path, "*:*.log*", False, True)):
        elog = Elog(filename)
        row = []
        for nCol in range(model.columnCount()):
            item = ModelItem(elog)
            item.markRead(filename in Elog.readflag)
            item.setData({Column.Flag: elog.filename in Elog.readflag,
                          Column.Category: elog.category,
                          Column.Package: elog.package,
                          Column.Eclass: elog.eclass,
                          Column.Date: elog.localeTime}[nCol],
                         role=Qt.DisplayRole)
            row.append(item)
        model.invisibleRootItem().appendRow(row)


class Elogviewer(QtGui.QMainWindow):

    def __init__(self, args):
        super(Elogviewer, self).__init__()
        self._args = args

        self.__initUI()
        self.__initToolBar()
        self.__initSettings()

        populate(self._model, self._args.elogpath)

    def __initUI(self):
        self._centralWidget = QtGui.QWidget(self)
        centralLayout = QtGui.QVBoxLayout()
        self._centralWidget.setLayout(centralLayout)
        self.setCentralWidget(self._centralWidget)

        self._tableView = QtGui.QTableView(self._centralWidget)
        self._tableView.setSelectionMode(self._tableView.ExtendedSelection)
        self._tableView.setSelectionBehavior(self._tableView.SelectRows)
        centralLayout.addWidget(self._tableView)

        self._model = QtGui.QStandardItemModel(self._tableView)
        self._model.setItemPrototype(ModelItem())
        self._model.setColumnCount(5)
        self._model.setHeaderData(Column.Flag, Qt.Horizontal, "Flag")
        self._model.setHeaderData(Column.Category, Qt.Horizontal, "Category")
        self._model.setHeaderData(Column.Package, Qt.Horizontal, "Package")
        self._model.setHeaderData(Column.Eclass, Qt.Horizontal, "Highest eclass")
        self._model.setHeaderData(Column.Date, Qt.Horizontal, "Timestamp")
        self._model.setSortRole(Role.SortRole)
        self._tableView.setModel(self._model)

        horizontalHeader = self._tableView.horizontalHeader()
        horizontalHeader.setSortIndicatorShown(True)
        horizontalHeader.setClickable(True)
        horizontalHeader.sortIndicatorChanged.connect(self._model.sort)
        horizontalHeader.setResizeMode(horizontalHeader.Stretch)

        self._textEdit = QtGui.QTextEdit(self._centralWidget)
        self._textEdit.setReadOnly(True)
        self._textEdit.setText("""No elogs!""")
        centralLayout.addWidget(self._textEdit)

        self._textWidgetMapper = QtGui.QDataWidgetMapper(self._tableView)
        self._textWidgetMapper.setSubmitPolicy(
            self._textWidgetMapper.AutoSubmit)
        self._textWidgetMapper.setItemDelegate(TextToHtmlDelegate(
            self._textWidgetMapper))
        self._textWidgetMapper.setModel(self._model)
        self._textWidgetMapper.addMapping(self._textEdit, 0)
        self._textWidgetMapper.toFirst()
        self._tableView.selectionModel().currentRowChanged.connect(
            self._textWidgetMapper.setCurrentModelIndex)
        self._tableView.selectionModel().currentRowChanged.connect(
            self.markPreviousItemRead)

    def __initToolBar(self):
        # see http://standards.freedesktop.org/icon-naming-spec/
        #   icon-naming-spec-latest.html#names
        # http://www.qtcentre.org/wiki/index.php?title=Embedded_resources
        # http://doc.trolltech.com/latest/qstyle.html#StandardPixmap-enum

        self._toolBar = QtGui.QToolBar(self)
        self.addToolBar(self._toolBar)

        self._refreshAction = QtGui.QAction("Refresh", self._toolBar)
        self._refreshAction.setIcon(QtGui.QIcon.fromTheme("view-refresh"))
        self._refreshAction.setShortcut(QtGui.QKeySequence.Refresh)
        self._refreshAction.triggered.connect(self.refresh)
        self._toolBar.addAction(self._refreshAction)

        self._markReadAction = QtGui.QAction("Mark read", self._toolBar)
        self._markReadAction.setIcon(QtGui.QIcon.fromTheme("mail-mark-read"))
        self._markReadAction.triggered.connect(partial(
            self._markSelectedRead, True))
        self._toolBar.addAction(self._markReadAction)

        self._markUnreadAction = QtGui.QAction("Mark unread", self._toolBar)
        self._markUnreadAction.setIcon(QtGui.QIcon.fromTheme("mail-mark-unread"))
        self._markUnreadAction.triggered.connect(partial(
            self._markSelectedRead, False))
        self._toolBar.addAction(self._markUnreadAction)

        self._markImportantAction = QtGui.QAction("Important", self._toolBar)
        self._markImportantAction.setIcon(QtGui.QIcon.fromTheme("mail-mark-important"))
        self._toolBar.addAction(self._markImportantAction)

        self._deleteAction = QtGui.QAction("Delete", self._toolBar)
        self._deleteAction.setIcon(QtGui.QIcon.fromTheme("edit-delete"))
        self._deleteAction.setShortcut(QtGui.QKeySequence.Delete)
        self._deleteAction.triggered.connect(self.deleteSelected)
        self._toolBar.addAction(self._deleteAction)

        self._aboutAction = QtGui.QAction("About", self._toolBar)
        self._aboutAction.setIcon(QtGui.QIcon.fromTheme("help-about"))
        self._aboutAction.setShortcut(QtGui.QKeySequence.HelpContents)
        self._aboutAction.triggered.connect(partial(
            QtGui.QMessageBox.about,
            self, "About (k)elogviewer", " ".join((
                """
                <h1>(k)elogviewer %s</h1>
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

                """ % __version__).splitlines())))
        self._toolBar.addAction(self._aboutAction)

        self._quitAction = QtGui.QAction("Quit", self._toolBar)
        self._quitAction.setIcon(QtGui.QIcon.fromTheme("application-exit"))
        self._quitAction.setShortcut(QtGui.QKeySequence.Quit)
        self._quitAction.triggered.connect(self.close)
        self._toolBar.addAction(self._quitAction)

    def __initSettings(self):
        self._settings = QtCore.QSettings("Mathias Laurin", "elogviewer")
        if not self._settings.contains("readflag"):
            self._settings.setValue("readflag", set())
        Elog.readflag = self._settings.value("readflag")

    def closeEvent(self, closeEvent):
        self._settings.setValue("readflag", Elog.readflag)
        super(Elogviewer, self).closeEvent(closeEvent)

    def markPreviousItemRead(self, current, previous):
        if not previous.isValid():
            return
        for nCol in range(self._model.columnCount()):
            self._model.item(previous.row(), nCol).markRead()

    def deleteSelected(self):
        selection = self._tableView.selectionModel().selectedRows()
        selectedRows = sorted(idx.row() for idx in selection)
        selectedElogs = [self._model.itemFromIndex(idx).elog()
                         for idx in selection]

        for nRow in reversed(selectedRows):
            self._model.removeRow(nRow)

        for elog in selectedElogs:
            elog.delete()

    def _markSelectedRead(self, markRead=True):
        for item in (self._model.itemFromIndex(idx) for idx
                     in self._tableView.selectionModel().selectedIndexes()):
            item.markRead(markRead)

    def refresh(self):
        self._model.removeRows(0, self._model.rowCount())
        populate(self._model, self._args.elogpath)


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
    if args.elogpath is None:
        logdir = portage.settings.get(
            "PORT_LOGDIR",
            os.path.join(os.sep, portage.settings["EPREFIX"],
                         *"var/log/portage".split("/")))
        args.elogpath = os.path.join(logdir, "elog")

    app = QtGui.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon.fromTheme("applications-system"))

    elogviewer = Elogviewer(args)
    elogviewer.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
