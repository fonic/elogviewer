#!/usr/bin/env python

# vi:ts=4 st=4 sw=4 et
# (c) 2010 Mathias Laurin, GPL2
# see elogviewerCommon.py for details

import sys
import core as ev
def main(argv):
    cmdline = ev.CommandLineArguments(argv)

    if cmdline.gui_frontend == "QT":
        from ev_qt.elogviewer import ElogviewerQt as ElogviewerGui
        from ev_qt.elogviewer import Filter
        from PyQt4 import QtGui
        global app
        app = QtGui.QApplication(sys.argv)
    else:
        from ev_gtk.elogviewer import ElogviewerGtk as ElogviewerGui
        from ev_gtk.elogviewer import Filter
    
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

    if cmdline.gui_frontend == "QT":
        sys.exit(app.exec_())
    elif cmdline.gui_frontend == "GTK":
        elogviewer.main()

if __name__ == "__main__":
    main(sys.argv[1:])

