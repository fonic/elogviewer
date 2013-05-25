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


class Filter:
    def __init__(self, label, match="", is_class=False, color='black'):
        self.name = label
        self.match = match if match else label
        self._is_class = is_class
        self.color = color
        self.button = QtGui.QCheckBox(label)
        self.button.setCheckState(QtCore.Qt.Checked)

    def is_active(self):
        return self.button.checkState() != 0

    def is_class(self):
        return self._is_class


class ElogContentPart:
    def __init__(self, complete_header):
        self.header = complete_header[0]
        self.section = complete_header[1]
        self.content = '%s (%s)\n' % (self.header, self.section)

    def add_content(self, content):
        self.content = ''.join([self.content, content, '\n'])


class Elog:
    def __init__(self, filename, elog_dir, filter_list):
        self.filename = filename
        self.filter_list = filter_list
        self.eclass = "einfo"
        self.contents = []

        basename = os.path.basename(filename)
        split_filename = basename.split(":")
        if len(split_filename) is 3:
            self.category, self.package, date = split_filename
        if len(split_filename) is 2:
            self.category = os.path.dirname(filename).split("/")[-1]
            self.package, date = split_filename
        date = time.strptime(date, "%Y%m%d-%H%M%S.log")
        self.sorted_time = time.strftime("%Y-%m-%d %H:%M:%S", date)
        self.locale_time = time.strftime("%x %X", date)

        self.read_file()

    def read_file(self):
        with open(self.filename, 'r') as f:
            file_contents = f.read()
            self.get_class(file_contents)
            self.get_contents(file_contents)

    def get_class(self, file_contents):
        '''Get the highest elog class
        adapted from Luca Marturana's elogv
        '''
        classes = re.findall("LOG:|INFO:|WARN:|ERROR:", file_contents)

        if "ERROR:" in classes:
            self.eclass = "eerror"
        elif "WARN:" in classes:
            self.eclass = "ewarn"
        elif "LOG:" in classes:
            self.eclass = "elog"

    def get_contents(self, file_contents):
        now = -1
        for line in file_contents.splitlines():
            L = line.split(': ')
            if len(L) is 2 and (L[0] and L[1]) in self.filter_list.keys():
                now += 1
                self.contents.append(ElogContentPart(L))
            else:
                self.contents[now].add_content(line)

    def delete(self):
        os.remove(self.filename)


class Elogviewer:

    def __init__(self, args):
        self._args = args
        self.selected_elog = None
        self.filter_list = {}

        self.filter_counter_class = self.filter_counter_stage = 0
        self.filter_columns_class = self.filter_columns_stage = 2

    def add_filter(self, filter):
        self.filter_list[filter.match] = filter
        if filter.is_class():
            t, l = divmod(self.filter_counter_class, self.filter_columns_class)
            self.filter_counter_class += 1
        else:
            t, l = divmod(self.filter_counter_stage, self.filter_columns_stage)
            self.filter_counter_stage += 1
        return (t, l)

    def populate(self):
        for filename in all_files(self._args.elogpath, '*:*.log',
                                  False, True):
            self.model.EVappend(Elog(filename,
                                     self._args.elogpath,
                                     self.filter_list))


class Role(object):

    ElogPath = Qt.UserRole + 1


class ElogModelItem(QtGui.QStandardItem):

    def __init__(self):
        super(ElogModelItem, self).__init__()
        self.__elogPath = None

    def type(self):
        return self.UserType

    def clone(self):
        return self.__class__()

    def elogPath(self):
        return self.data(role=Role.ElogPath)

    def setElogPath(self, elogPath):
        self.setData(elogPath, role=Role.ElogPath)


class Model(QtGui.QStandardItemModel):

    def __init__(self, parent=None):
        super(Model, self).__init__(parent)
        self.setItemPrototype(ElogModelItem())

        self.setColumnCount(4)
        self.setHeaderData(CATEGORY, QtCore.Qt.Horizontal, "Category")
        self.setHeaderData(PACKAGE, QtCore.Qt.Horizontal, "Package")
        self.setHeaderData(ECLASS, QtCore.Qt.Horizontal, "Highest eclass")
        self.setHeaderData(TIMESTAMP, QtCore.Qt.Horizontal, "Timestamp")
        self.setHeaderData(ELOG, QtCore.Qt.Horizontal, "Elog")
        self.setSortRole(SORT)

        # maintain separate list of elog
        self.elog_dict = {}

    def populate(self, path):
        for filename in all_files(path, "*:*.log", False, True):
            print(filename)
            #self.appendRow(Elog(filename, path, []))  # XXX

    def EVappend(self, elog):
        print("deprecated")  # XXX

    def appendRow(self, elog):
        self.elog_dict[elog.filename] = elog

        category_it = QtGui.QStandardItem(elog.category)
        category_it.setData(QtCore.QVariant(elog.category), SORT)

        package_it = QtGui.QStandardItem(elog.package)
        package_it.setData(QtCore.QVariant(elog.package), SORT)
        package_it.setData(QtCore.QVariant(elog.filename), FILENAME)

        eclass_it = QtGui.QStandardItem(elog.eclass)
        eclass_it.setData(QtCore.QVariant(elog.eclass), SORT)

        time_it = QtGui.QStandardItem(elog.locale_time)
        time_it.setData(QtCore.QVariant(elog.sorted_time), SORT)

        elog_it = ElogModelItem(elog)
        return QtGui.QStandardItemModel.appendRow(self,
                [category_it, package_it, eclass_it, time_it])

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        for current_row in xrange(row, row + count):
            idx = self.index(current_row, PACKAGE, parent)
            filename = str(idx.data(FILENAME).toString())
            if filename in self.elog_dict:
                del self.elog_dict[filename]
        return QtGui.QStandardItemModel.removeRows(self, row, count, parent)


class ElogviewerQt(QtGui.QMainWindow, Elogviewer):

    def __init__(self, args):
        QtGui.QMainWindow.__init__(self)
        Elogviewer.__init__(self, args)
        self.display_elog = None

        self.__initUI()
        self.__initToolBar()

        self._treeView.model().populate(self._args.elogpath)

    def __initUI(self):
        self._centralWidget = QtGui.QWidget(self)
        centralLayout = QtGui.QVBoxLayout()
        self._centralWidget.setLayout(centralLayout)
        self.setCentralWidget(self._centralWidget)

        self._treeView = QtGui.QTreeView(self._centralWidget)
        self._treeView.setRootIsDecorated(False)
        self._treeView.setColumnHidden(ELOG, True)
        self._treeView.setSelectionMode(self._treeView.ExtendedSelection)
        centralLayout.addWidget(self._treeView)

        self._model = Model()
        self._treeView.setModel(self._model)
        self._treeView.selectionModel().selectionChanged.connect(
            self.on_selection_changed)

        treeViewHeader = self._treeView.header()
        treeViewHeader.setSortIndicatorShown(True)
        treeViewHeader.setClickable(True)
        treeViewHeader.sortIndicatorChanged.connect(self._model.sort)

        bottomLayout = QtGui.QHBoxLayout()
        centralLayout.addLayout(bottomLayout)

        self._textEdit = QtGui.QTextEdit(self._centralWidget)
        self._textEdit.setReadOnly(True)
        self._textEdit.setHtml("""<h1>hello world</h1>""")
        bottomLayout.addWidget(self._textEdit)

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

        self._quitAction = QtGui.QAction("Quit", self._toolBar)
        self._toolBar.addAction(self._quitAction)

    def create_gui(self):
        self.show()

    def on_selection_changed(self, new_selection, old_selection):
        idx_list = new_selection.indexes()
        if not idx_list:
            msg = "0 of %i, no selection" % self._model.rowCount()
            self.display_elog = None
            self.read_elog()
        elif len(idx_list) is self._model.columnCount():
            idx = idx_list[PACKAGE]
            filename = str(idx.data(FILENAME).toString())
            msg = "%i of %i, %s" % (
                    idx.row() + 1,
                    self._model.rowCount(),
                    filename)
            self.display_elog = self._model.elog_dict[filename]
            self.read_elog()
        else:
            msg = "Multiple selections"
        self.gui.statusbar.showMessage(msg)

    def on_actionDelete_triggered(self, checked=None):
        if checked is None:
            return
        idx_list = self.gui.treeView.selectionModel().selectedRows(PACKAGE)
        idx_list.reverse()
        for idx in idx_list:
            filename = str(idx.data(FILENAME).toString())
            self._model.elog_dict[filename].delete()
            self._model.removeRow(idx.row())

    def show(self):
        QtGui.QMainWindow.show(self)
        return  # XXX
        self.read_elog()

    def refresh(self):
        self._model.removeRows(0, self._model.rowCount())
        self.populate()

    def add_filter(self, filter):
        return  # XXX
        filter.button.connect(filter.button,
                              QtCore.SIGNAL("stateChanged(int)"),
                              self.read_elog)
        t, l = Elogviewer.add_filter(self, filter)

        filter_table = self.gui.filter_class_layout if filter.is_class() \
                else self.gui.filter_stage_layout
        filter_table.addWidget(filter.button, t, l)

    def read_elog(self):
        self.gui.textEdit.clear()
        if self.display_elog is None:
            buf = '''
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
(k)elogviewer application icon (c) gnome, GPL2
'''
        else:
            buf = ''.join('<p style="color: %s">%s</p>' %
                (self.filter_list[elog_part.header].color, elog_part.content)
                for elog_part in self.display_elog.contents
                if self.filter_list[elog_part.header].is_active()
                and self.filter_list[elog_part.section].is_active())
            buf = buf.replace('\n', '<br>')
        self.gui.textEdit.append(buf)
        self.gui.textEdit.verticalScrollBar().setValue(0)


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

    elogviewer = ElogviewerQt(args)
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

    elogviewer.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
