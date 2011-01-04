#!/usr/bin/env python

# vi:ts=4 st=4 sw=4 et
# (c) 2010 Mathias Laurin, GPL2
# see elogviewerCommon.py for details

import sys
from elogviewerCommon import parseArguments
def main(argv):
	cmdline = parseArguments(argv)

	if cmdline.get_gui_frontend() == "QT":
		from elogviewerQt import ElogviewerQt as ElogviewerGui
		from elogviewerQt import Filter
		from PyQt4 import QtGui
		global app
		app = QtGui.QApplication(sys.argv)
	else:
		from elogviewerGtk import ElogviewerGtk as ElogviewerGui
		from elogviewerGtk import Filter
	
	elogviewer = ElogviewerGui(cmdline)
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

	elogviewer.connect()
	elogviewer.show()
	elogviewer.refresh()
	elogviewer.main()

	if cmdline.get_gui_frontend() == "QT":
		sys.exit(app.exec_())

if __name__ == "__main__":
	main(sys.argv[1:])

