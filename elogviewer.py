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
import logging
import argparse
import locale
import time
import re
from math import cos, sin
from glob import glob
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
    import sip as _sip
    for _type in "QDate QDateTime QString QVariant".split():
        _sip.setapi(_type, 2)
    from PyQt4 import QtCore, QtGui
except ImportError:
    from PySide import QtCore, QtGui

Qt = QtCore.Qt

try:
    import portage
except ImportError:
    portage = None


__version__ = "2.0"


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

    Important = 0
    Category = 1
    Package = 2
    Flag = 3
    Eclass = 4
    Date = 5


class Elog(object):

    _readFlag = set()
    _importantFlag = set()

    def __init__(self, filename):
        self.filename = _to_string(filename)
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
        Elog._readFlag.remove(self.filename)

    @property
    def file(self):
        root, ext = os.path.splitext(self.filename)
        try:
            return {".gz": gzip.open,
                    ".bz2": bz2.BZ2File,
                    ".log": open}[ext](self.filename, "rb")
        except KeyError:
            logging.error("%s: unsupported format" % self.filename)
            return closing(StringIO(
                """
                <!-- set eclass: ERROR: -->
                <h2>Unsupported format</h2>
                The selected elog is in an unsupported format.
                """
            ))
        except IOError:
            logging.error("%s: could not open file" % self.filename)
            return closing(StringIO(
                """
                <!-- set eclass: ERROR: -->
                <h2>File does not open</h2>
                The selected elog could not be opened.
                """
            ))

    @property
    def htmltext(self):
        htmltext = []
        with self.file as elogfile:
            for line in elogfile:
                line = _to_string(line.strip())
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
    def importantFlag(self):
        return self.filename in Elog._importantFlag

    @importantFlag.setter
    def importantFlag(self, flag):
        if flag:
            Elog._importantFlag.add(self.filename)
        else:
            try:
                Elog._importantFlag.remove(self.filename)
            except KeyError:
                pass

    @property
    def isoTime(self):
        return time.strftime("%Y-%m-%d %H:%M:%S", self.date)

    @property
    def localeTime(self):
        return time.strftime("%x %X", self.date)

    @property
    def readFlag(self):
        return self.filename in Elog._readFlag

    @readFlag.setter
    def readFlag(self, flag):
        if flag:
            Elog._readFlag.add(self.filename)
        else:
            try:
                Elog._readFlag.remove(self.filename)
            except KeyError:
                pass


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


class Bullet(QtGui.QAbstractButton):

    _scaleFactor = 20

    def __init__(self, parent=None):
        super(Bullet, self).__init__(parent)
        self.setAttribute(Qt.WA_NoSystemBackground)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        green = QtGui.QBrush(Qt.darkGreen)
        painter.setBrush(self.palette().dark() if self.isChecked() else green)
        rect = event.rect()
        painter.translate(rect.x(), rect.y())
        painter.scale(self._scaleFactor, self._scaleFactor)
        painter.drawEllipse(QtCore.QRectF(0.5, 0.5, 0.5, 0.5))


class Star(QtGui.QAbstractButton):
    # Largely inspired by Nokia's stardelegate example.

    _scaleFactor = 20

    def __init__(self, parent=None):
        super(Star, self).__init__(parent)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self._starPolygon = QtGui.QPolygonF([QtCore.QPointF(1.0, 0.5)])
        for i in range(5):
            self._starPolygon << QtCore.QPointF(
                0.5 + 0.5 * cos(0.8 * i * 3.14),
                0.5 + 0.5 * sin(0.8 * i * 3.14))

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)
        red = QtGui.QBrush(Qt.red)
        painter.setBrush(self.palette().dark() if self.isChecked() else red)
        rect = event.rect()
        yOffset = (rect.height() - self._scaleFactor) / 2.0
        painter.translate(rect.x(), rect.y() + yOffset)
        painter.scale(self._scaleFactor, self._scaleFactor)
        painter.drawPolygon(self._starPolygon, QtCore.Qt.WindingFill)


class ButtonDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, button=None, parent=None):
        super(ButtonDelegate, self).__init__(parent)
        self._btn = QtGui.QPushButton() if button is None else button
        self._btn.setParent(parent)
        self._btn.setCheckable(True)
        self._btn.hide()

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.parent())

    def sizeHint(self, option, index):
        return super(ButtonDelegate, self).sizeHint(option, index)

    def createEditor(self, parent, option, index):
        return None

    def setModelData(self, editor, model, index):
        model.setData(index, editor.isChecked())

    def paint(self, painter, option, index):
        self._btn.setChecked(index.data())
        self._btn.setGeometry(option.rect)
        if option.state & QtGui.QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        pixmap = QtGui.QPixmap.grabWidget(self._btn)
        painter.drawPixmap(option.rect.x(), option.rect.y(), pixmap)

    def editorEvent(self, event, model, option, index):
        if (int(index.flags()) & Qt.ItemIsEditable and
            (event.type() in (QtCore.QEvent.MouseButtonRelease,
                              QtCore.QEvent.MouseButtonDblClick) and
             event.button() == Qt.LeftButton) or
            (event.type() == QtCore.QEvent.KeyPress and
             event.key() in (Qt.Key_Space, Qt.Key_Select))):
                self._btn.toggle()
                self.setModelData(self._btn, model, index)
                self.commitData.emit(self._btn)
                return True
        return False


class ElogItem(QtGui.QStandardItem):

    def __init__(self, elog=None):
        super(ElogItem, self).__init__()
        self.__elog = elog

    def type(self):
        return self.UserType + 1

    def clone(self):
        return self.__class__()

    def elog(self):
        return self.__elog

    def setReadFlag(self, readFlag=True):
        self.__elog.readFlag = readFlag

        font = self.font()
        font.setBold(not readFlag)
        self.setFont(font)

    def readFlag(self):
        return self.__elog.readFlag

    def setImportantFlag(self, importantFlag=True):
        self.setData(importantFlag, role=Qt.EditRole)

    def importantFlag(self):
        return self.__elog.importantFlag

    def data(self, role=Qt.UserRole + 1):
        if not self.__elog:
            return super(ElogItem, self).data(role)
        if role is Role.SortRole:
            if self.column() == Column.Date:
                return self.__elog.isoTime
            else:
                return self.data(role=Qt.DisplayRole)
        if role in (Qt.DisplayRole, Qt.EditRole):
            return {Column.Important: self.__elog.importantFlag,
                    Column.Flag: self.__elog.readFlag,
                    Column.Category: self.__elog.category,
                    Column.Package: self.__elog.package,
                    Column.Eclass: self.__elog.eclass,
                    Column.Date: self.__elog.localeTime}[self.column()]
        else:
            return super(ElogItem, self).data(role)

    def setData(self, data, role=Qt.UserRole + 1):
        if not self.__elog:
            return super(ElogItem, self).setData(data, role)
        if role in (Qt.DisplayRole, Qt.EditRole):
            if self.column() is Column.Important:
                self.__elog.importantFlag = data
            elif self.column() is Column.Flag:
                self.__elog.readFlag = data
        super(ElogItem, self).setData(data, role)


def populate(model, path):
    for filename in (glob(os.path.join(path, "*:*:*.log*")) +
                     glob(os.path.join(path, "*", "*:*.log*"))):
        elog = Elog(filename)
        row = []
        for nCol in range(model.columnCount()):
            item = ElogItem(elog)
            item.setReadFlag(elog.readFlag)
            if nCol is Column.Important:
                item.setEditable(True)
            else:
                item.setEditable(False)
            row.append(item)
        model.appendRow(row)


class Elogviewer(QtGui.QMainWindow):

    def __init__(self, args):
        super(Elogviewer, self).__init__()
        self._args = args

        self.__initUI()
        self.__initToolBar()
        self.__initSettings()

        def populateAndInit(model, path):
            populate(model, path)
            self._tableView.selectionModel().currentRowChanged.emit(
                QtCore.QModelIndex(), QtCore.QModelIndex())

        QtCore.QTimer.singleShot(0, partial(
            populateAndInit, self._model, self._args.elogpath))

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
        self._model.setItemPrototype(ElogItem())
        self._model.setColumnCount(6)
        self._model.setHeaderData(Column.Important, Qt.Horizontal, "Important")
        self._model.setHeaderData(Column.Flag, Qt.Horizontal, "Read")
        self._model.setHeaderData(Column.Category, Qt.Horizontal, "Category")
        self._model.setHeaderData(Column.Package, Qt.Horizontal, "Package")
        self._model.setHeaderData(Column.Eclass, Qt.Horizontal, "Highest eclass")
        self._model.setHeaderData(Column.Date, Qt.Horizontal, "Timestamp")
        self._model.setSortRole(Role.SortRole)

        self._proxyModel = QtGui.QSortFilterProxyModel(self._tableView)
        self._proxyModel.setFilterKeyColumn(-1)
        self._proxyModel.setSourceModel(self._model)

        self._tableView.setModel(self._proxyModel)
        self._tableView.setItemDelegateForColumn(
            Column.Important, ButtonDelegate(Star(), self._tableView))
        self._tableView.setItemDelegateForColumn(
            Column.Flag, ButtonDelegate(Bullet(), self._tableView))

        horizontalHeader = self._tableView.horizontalHeader()
        horizontalHeader.setSortIndicatorShown(True)
        horizontalHeader.setClickable(True)
        horizontalHeader.sortIndicatorChanged.connect(self._model.sort)
        horizontalHeader.setResizeMode(horizontalHeader.Stretch)

        self._tableView.verticalHeader().hide()

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

        self._statusLabel = QtGui.QLabel(self.statusBar())
        self.statusBar().addWidget(self._statusLabel)
        self._unreadLabel = QtGui.QLabel(self.statusBar())
        self.statusBar().addWidget(self._unreadLabel)

        currentRowChanged = self._tableView.selectionModel().currentRowChanged
        currentRowChanged.connect(
            lambda cur: self._textWidgetMapper.setCurrentModelIndex(
                self._proxyModel.mapToSource(cur)))
        currentRowChanged.connect(
            lambda cur, prev: self.markPreviousItemRead(
                *map(self._proxyModel.mapToSource, (cur, prev))))
        currentRowChanged.connect(
            lambda cur: self._statusLabel.setText(
                "%i of %i elogs" % (cur.row() + 1, self._model.rowCount())))
        currentRowChanged.connect(
            lambda __: self.setWindowTitle("Elogviewer (%i unread)" % (
                self._model.rowCount() - len(Elog._readFlag))))
        currentRowChanged.connect(
            lambda __: self._unreadLabel.setText("%i unread" %(
                self._model.rowCount() - len(Elog._readFlag))))

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

                """ % __version__).splitlines())))
        self._toolBar.addAction(self._aboutAction)

        self._quitAction = QtGui.QAction("Quit", self._toolBar)
        self._quitAction.setIcon(QtGui.QIcon.fromTheme("application-exit"))
        self._quitAction.setShortcut(QtGui.QKeySequence.Quit)
        self._quitAction.triggered.connect(self.close)
        self._toolBar.addAction(self._quitAction)

        self._searchLineEdit = QtGui.QLineEdit(self._toolBar)
        self._searchLineEdit.setPlaceholderText("search")
        self._searchLineEdit.textEdited.connect(
            self._proxyModel.setFilterRegExp)
        self._toolBar.addWidget(self._searchLineEdit)

    def __initSettings(self):
        self._settings = QtCore.QSettings("Mathias Laurin", "elogviewer")
        try:
            Elog._readFlag = self._settings.value("readFlag", set())
            Elog._importantFlag = self._settings.value("importantFlag", set())
            if Elog._readFlag is None or Elog._importantFlag is None:
                raise TypeError
        except TypeError:
            # The list is lost when going from py3 to py2
            logging.error("The settings message could not be loaded.")
            Elog._readFlag = set()
            Elog._importantFlag = set()

    def closeEvent(self, closeEvent):
        self._settings.setValue("readFlag", Elog._readFlag)
        self._settings.setValue("importantFlag", Elog._importantFlag)
        super(Elogviewer, self).closeEvent(closeEvent)

    def markPreviousItemRead(self, current, previous):
        if not previous.isValid():
            return
        for nCol in range(self._model.columnCount()):
            self._model.item(previous.row(), nCol).setReadFlag()

    def deleteSelected(self):
        selection = [self._proxyModel.mapToSource(idx) for idx in
                     self._tableView.selectionModel().selectedRows()]
        selectedRows = sorted(idx.row() for idx in selection)
        selectedElogs = [self._model.itemFromIndex(idx).elog()
                         for idx in selection]

        for nRow in reversed(selectedRows):
            self._model.removeRow(nRow)

        for elog in selectedElogs:
            elog.delete()

    def _markSelectedRead(self, readFlag=True):
        selection = (self._proxyModel.mapToSource(idx) for idx in
                     self._tableView.selectionModel().selectedIndexes())
        for item in (self._model.itemFromIndex(idx) for idx in selection):
            item.setReadFlag(readFlag)

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
    parser.add_argument("--log", choices="DEBUG INFO WARNING ERROR".split(),
                        default="WARNING", help="set logging level")
    args = parser.parse_args()
    if args.elogpath is None:
        logdir = portage.settings.get(
            "PORT_LOGDIR",
            os.path.join(os.sep, portage.settings["EPREFIX"],
                         *"var/log/portage".split("/")))
        args.elogpath = os.path.join(logdir, "elog")
    getattr(logging, args.log.upper())

    app = QtGui.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon.fromTheme("applications-system"))

    elogviewer = Elogviewer(args)
    elogviewer.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
