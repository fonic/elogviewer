#!/usr/bin/env python

# (c) 2011 Mathias Laurin, GPL2
# see libelogviewer/core.py for details

import sys
import os
import getopt
import portage


help_msg = """Elogviewer should help you not to miss important information like:

If you have just upgraded from an older version of python you
will need to run:
    /usr/sbin/python-updater

please do run it and restart elogviewer.
"""


usage_msg = """You need to enable the elog feature by setting at least one of
    PORTAGE_ELOG_CLASSES="info warn error log qa"
and
    PORTAGE_ELOG_SYSTEM="save"
in /etc/make.conf

You need to add yourself to the portage group to use
elogviewer without privileges.

Read /etc/make.conf.example for more information
"""


class CommandLineArguments:
    def __init__(self, argv):
        # default arguments
        self.debug = False
        self.elog_dir = portage.settings["PORT_LOGDIR"]
        if not self.elog_dir:
            self.elog_dir = "/var/log/portage"
        self.gui_frontend = "GTK"  # GTK or QT

        # parse commandline
        try:
            opts, args = getopt.getopt(argv,
                    "dhgqp:", ["debug", "help", "gtk", "qt", "elogpath"])
        except getopt.GetoptError:
            print help_msg
            print usage_msg
            exit(1)
        for opt, arg in opts:
            if opt in ("-d", "--debug"):
                self.debug = True
                print "debug mode is set"
            elif opt in ("-q", "--qt"):
                self.gui_frontend = "QT"
            elif opt in ("-h", "--help"):
                print help_msg
                print usage_msg
                exit(0)
            elif opt in ("-p", "--elogpath"):
                self.elog_dir = arg

        # post process arguments
        elog_dir = "/".join([self.elog_dir, "elog", ""])
        if os.path.isdir(elog_dir):
            self.elog_dir = elog_dir


def main(argv):
    cmdline = CommandLineArguments(argv)

    if cmdline.gui_frontend == "QT":
        from libelogviewer.ev_qt.elogviewer import ElogviewerQt as ElogviewerGui
        from libelogviewer.ev_qt.elogviewer import Filter
        from PyQt4 import QtGui
        global app
        app = QtGui.QApplication(sys.argv)
    else:
        from libelogviewer.ev_gtk.elogviewer import ElogviewerGtk as ElogviewerGui
        from libelogviewer.ev_gtk.elogviewer import Filter

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
