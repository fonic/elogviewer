#!/usr/bin/env python

# (c) 2011, 2013 Mathias Laurin, GPLv2
# see libelogviewer/core.py for details

import sys
import os
import argparse

try:
    import portage
except ImportError:
    portage = None


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
    gui_arg = parser.add_mutually_exclusive_group()
    gui_arg.add_argument("-q", "--qt", action="store_true",
                         help="start with the Qt interface")
    gui_arg.add_argument("-g", "--gtk", action="store_true",
                         help="start with the Gtk interface")
    args = parser.parse_args()

    if args.qt:
        from libelogviewer.ev_qt.elogviewer import ElogviewerQt as ElogviewerGui
        from libelogviewer.ev_qt.elogviewer import Filter
        from PyQt4 import QtGui
        global app
        app = QtGui.QApplication(sys.argv)
    else:
        from libelogviewer.ev_gtk.elogviewer import ElogviewerGtk as ElogviewerGui
        from libelogviewer.ev_gtk.elogviewer import Filter

    elogviewer = ElogviewerGui(args)
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

    if args.qt:
        sys.exit(app.exec_())
    else:
        elogviewer.main()

if __name__ == "__main__":
    main()
