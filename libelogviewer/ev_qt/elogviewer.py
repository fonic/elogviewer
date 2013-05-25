# (c) 2011, 2013 Mathias Laurin, GPL2
# see libelogviewer/core.py for details

from PyQt4 import QtCore, QtGui
import libelogviewer.core as core


class ElogInstanceItem(QtGui.QStandardItem):
    def __init__(self, elog):
        QtGui.QStandardItem.__init__(self)
        self.elog = elog

    def type(self):
        return 1000


CATEGORY, PACKAGE, ECLASS, TIMESTAMP, ELOG = range(5)
SORT = QtCore.Qt.UserRole
FILENAME = QtCore.Qt.UserRole + 1


class Model(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, parent)
        self.setColumnCount(4)
        self.setHeaderData(CATEGORY, QtCore.Qt.Horizontal, "Category")
        self.setHeaderData(PACKAGE, QtCore.Qt.Horizontal, "Package")
        self.setHeaderData(ECLASS, QtCore.Qt.Horizontal, "Highest eclass")
        self.setHeaderData(TIMESTAMP, QtCore.Qt.Horizontal, "Timestamp")
        self.setHeaderData(ELOG, QtCore.Qt.Horizontal, "Elog")
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

        eclass_it = QtGui.QStandardItem(elog.eclass)
        eclass_it.setData(QtCore.QVariant(elog.eclass), SORT)

        time_it = QtGui.QStandardItem(elog.locale_time)
        time_it.setData(QtCore.QVariant(elog.sorted_time), SORT)

        elog_it = ElogInstanceItem(elog)
        return QtGui.QStandardItemModel.appendRow(self,
                [category_it, package_it, eclass_it, time_it])

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        for current_row in xrange(row, row + count):
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


class ElogviewerQt(QtGui.QMainWindow, core.Elogviewer):

    def __init__(self, args):
        QtGui.QMainWindow.__init__(self)
        core.Elogviewer.__init__(self, args)
        self.display_elog = None

        self.__initUI()
        self.__initToolBar()

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
        self.populate()
        self.read_elog()

    def refresh(self):
        self._model.removeRows(0, self._model.rowCount())
        self.populate()

    def add_filter(self, filter):
        return  # XXX
        filter.button.connect(filter.button,
                              QtCore.SIGNAL("stateChanged(int)"),
                              self.read_elog)
        t, l = core.Elogviewer.add_filter(self, filter)

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
