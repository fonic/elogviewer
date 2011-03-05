# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'elogviewer.ui'
#
# Created: Sat Mar  5 22:45:11 2011
#      by: PyQt4 UI code generator 4.8.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(800, 600)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.centralwidget)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.treeView = QtGui.QTreeView(self.centralwidget)
        self.treeView.setObjectName(_fromUtf8("treeView"))
        self.verticalLayout_2.addWidget(self.treeView)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.textEdit = QtGui.QTextEdit(self.centralwidget)
        self.textEdit.setReadOnly(True)
        self.textEdit.setHtml(_fromUtf8("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"></p></body></html>"))
        self.textEdit.setObjectName(_fromUtf8("textEdit"))
        self.horizontalLayout.addWidget(self.textEdit)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.filter_class_box = QtGui.QGroupBox(self.centralwidget)
        self.filter_class_box.setObjectName(_fromUtf8("filter_class_box"))
        self.gridLayout_4 = QtGui.QGridLayout(self.filter_class_box)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.filter_class_layout = QtGui.QGridLayout()
        self.filter_class_layout.setObjectName(_fromUtf8("filter_class_layout"))
        self.gridLayout_4.addLayout(self.filter_class_layout, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.filter_class_box)
        self.filter_stage_box = QtGui.QGroupBox(self.centralwidget)
        self.filter_stage_box.setObjectName(_fromUtf8("filter_stage_box"))
        self.gridLayout_5 = QtGui.QGridLayout(self.filter_stage_box)
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.filter_stage_layout = QtGui.QGridLayout()
        self.filter_stage_layout.setObjectName(_fromUtf8("filter_stage_layout"))
        self.gridLayout_5.addLayout(self.filter_stage_layout, 0, 0, 1, 1)
        self.verticalLayout.addWidget(self.filter_stage_box)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout_3.addLayout(self.verticalLayout_2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(MainWindow)
        self.toolBar.setObjectName(_fromUtf8("toolBar"))
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionQuit = QtGui.QAction(MainWindow)
        self.actionQuit.setObjectName(_fromUtf8("actionQuit"))
        self.actionDelete = QtGui.QAction(MainWindow)
        self.actionDelete.setObjectName(_fromUtf8("actionDelete"))
        self.actionRefresh = QtGui.QAction(MainWindow)
        self.actionRefresh.setObjectName(_fromUtf8("actionRefresh"))
        self.toolBar.addAction(self.actionRefresh)
        self.toolBar.addAction(self.actionDelete)
        self.toolBar.addAction(self.actionQuit)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.filter_class_box.setTitle(QtGui.QApplication.translate("MainWindow", "Class Filter", None, QtGui.QApplication.UnicodeUTF8))
        self.filter_stage_box.setTitle(QtGui.QApplication.translate("MainWindow", "Stage Filter", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("MainWindow", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setText(QtGui.QApplication.translate("MainWindow", "&Quit (k)elogviewer", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+Q", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDelete.setText(QtGui.QApplication.translate("MainWindow", "Delete", None, QtGui.QApplication.UnicodeUTF8))
        self.actionDelete.setShortcut(QtGui.QApplication.translate("MainWindow", "Del", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRefresh.setText(QtGui.QApplication.translate("MainWindow", "&Refresh", None, QtGui.QApplication.UnicodeUTF8))
        self.actionRefresh.setShortcut(QtGui.QApplication.translate("MainWindow", "Ctrl+R", None, QtGui.QApplication.UnicodeUTF8))

