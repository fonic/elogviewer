#!/usr/bin/env python

# vi:ts=4 st=4 sw=4 et
# (c) 2010 Mathias Laurin, GPL2
# see elogviewerCommon.py for details

# Redirect messages to stderr
import sys
sys.stdout = sys.stderr
import os.path as path

try:
    import gtk
    import gtk.glade
except:
    print "a recent version of pygtk is required"

import pango

import libelogviewer.core as core
 
( ELOG, CATEGORY, PACKAGE, TIMESTAMP, TIMESORT, FILENAME ) = range(6)
from gobject import TYPE_STRING, TYPE_PYOBJECT
class Model(gtk.ListStore):
    def __init__(self):
        gtk.ListStore.__init__(self,
            TYPE_PYOBJECT, TYPE_STRING, TYPE_STRING, TYPE_STRING, TYPE_STRING, TYPE_STRING )

	def EVappend(self, elog):
		self.append(elog)
    
    def append(self, elog):
        return gtk.ListStore.append(self, [elog, elog.category, elog.package,
            elog.locale_time, elog.sorted_time, elog.filename])
    
    def get_value(self, iter):
        return gtk.ListStore.get_value(self, iter, 0)


class Filter(core.Filter):
    def __init__(self, label, match="", is_class=False, color='black'):
        self.button = gtk.CheckButton(label)
        self.button.set_active(True)
        core.Filter.__init__(self, label, match, is_class, color)
    
    def is_active(self):
        return self.button.get_active()


class ElogviewerGtk(core.Elogviewer):

    def __init__(self, cmdline_args):
        core.Elogviewer.__init__(self)
        self.cmdline_args = cmdline_args
        self.model = Model()
        self.texttagtable = gtk.TextTagTable()
        self.selected_elog = None

    
    def create_gui(self):
        gladefile = '/'.join([path.split(__file__)[0], "elogviewer.glade"])
        self.gui = gtk.Builder()
        self.gui.add_from_file(gladefile)

        self.treeview = self.gui.get_object("treeview")
        self.treeview.set_model(self.model)

        category_col = gtk.TreeViewColumn(
            'Category', gtk.CellRendererText(), text=CATEGORY)
        package_col = gtk.TreeViewColumn(
            'Package', gtk.CellRendererText(), text=PACKAGE)
        locale_time_col = gtk.TreeViewColumn(
            'Time', gtk.CellRendererText(), text=TIMESTAMP)
        sorted_time_col = gtk.TreeViewColumn(
            'Sort time', gtk.CellRendererText(), text=TIMESORT)
        filename_col = gtk.TreeViewColumn(
            'Filename', gtk.CellRendererText(), text=FILENAME)

        category_col.set_sort_column_id(CATEGORY)
        package_col.set_sort_column_id(PACKAGE)
        locale_time_col.set_sort_column_id(TIMESORT)
        if not self.cmdline_args.debug:
            sorted_time_col.set_visible(False)
            filename_col.set_visible(False)

        self.treeview.append_column(category_col)
        self.treeview.append_column(package_col)
        self.treeview.append_column(locale_time_col)
        self.treeview.append_column(sorted_time_col)
        self.treeview.append_column(filename_col)
        self.treeview.set_enable_search(False)

        self.statusbar = self.gui.get_object("statusbar")

    def connect(self):
        self.gui.connect_signals({
            "on_window_destroy" : gtk.main_quit,
            "on_actionQuit_activate" : gtk.main_quit,
            "on_actionDelete_activate" : self.on_actionDelete,
            "on_actionRefresh_activate" : self.on_actionRefresh,
            "on_liststore_row_deleted": self.on_row_deleted
                    })
        self.gui.get_object("treeview").get_selection().connect(
                'changed', self.on_selection_changed)

    def on_selection_changed(self, selection):
        if selection.count_selected_rows() is not 0:
            (model, iter) = selection.get_selected()
            row = model.get_path(iter)[0] + 1
            self.selected_elog = model.get_value(iter)
        else:
            self.selected_elog = None
            row = 0
        self.update_statusbar(row)
        self.read_elog()
    
    def on_actionDelete(self, action=None):
        if self.selected_elog is None:
            return
        filename = self.selected_elog.filename
        if self.cmdline_args.debug:
            print "%s deleted" % str(filename)
        else:
            self.selected_elog.delete()
        iter = self.gui.get_object("treeview").get_selection().get_selected()[1]
        self.model.remove(iter)

    def on_row_deleted(self, model, path):
        selection = self.treeview.get_selection()
        path = path[0]
        if len(model) is not 0:
            if path is len(model):
                selection.select_path(path-1)
            else:
                selection.select_path(path)
    
    def on_actionRefresh(self, action):
        self.refresh()

    def show(self):
        main_window = self.gui.get_object("window")
        main_window.show()
        self.populate()
        self.update_statusbar()
        self.read_elog()

    def refresh(self):
        self.model.clear()
        self.populate()
		self.update_statusbar()

    def add_filter(self, filter):
        filter.button.connect('toggled', self.read_elog)
        (t, l) = core.Elogviewer.add_filter(self, filter)

        if filter.is_class():
			filter_table = self.gui.get_object("filter_class_table")
            tag = gtk.TextTag(filter.match)
            tag.set_property('foreground', filter.color)
            self.texttagtable.add(tag)
        else:
			filter_table = self.gui.get_object("filter_stage_table")
		filter_table.attach(filter.button, l, l+1, t, t+1)
        filter.button.show()

    def read_elog(self, *arg):
        if self.selected_elog is None:
            header1 = gtk.TextTag('header1')
            header1.set_property("weight", pango.WEIGHT_BOLD)
            header1.set_property("scale", pango.SCALE_XX_LARGE)
            header2 = gtk.TextTag('header2')
            header2.set_property("weight", pango.WEIGHT_BOLD)
            header2.set_property("scale", pango.SCALE_LARGE)
            small = gtk.TextTag('small')
            small.set_property("scale", pango.SCALE_SMALL)
            center = gtk.TextTag('center')
            center.set_property("justification", gtk.JUSTIFY_CENTER)
            link = gtk.TextTag('link')
            tag_table = gtk.TextTagTable()
            [ tag_table.add(tag) for tag in 
                    [header1, header2, small, center, link] ]
            buf = gtk.TextBuffer(tag_table)
            buf.insert_with_tags(buf.get_end_iter(), 
                    '(k)elogviewer 1.0.0\n', header1)
            buf.insert_with_tags(buf.get_end_iter(), 
'\n(k)elogviewer, copyright (c) 2007, 2011 Mathias Laurin\n\
kelogviewer, copyright (c) 2007 Jeremy Wickersheimer\n\
GNU General Public License (GPL) version 2\n', small, center)
            buf.insert_with_tags(buf.get_end_iter(), 
'<http://sourceforge.net/projects/elogviewer>\n', center)
            buf.insert_with_tags(buf.get_end_iter(), 
                    '\nWritten by\n\n', header2)
            buf.insert_with_tags(buf.get_end_iter(), 
'Mathias Laurin <mathias_laurin@users.sourceforge.net>\n\
Timothy Kilbourn (initial author)\n\
Jeremy Wickersheimer (qt3/KDE port)\n')
            buf.insert_with_tags(buf.get_end_iter(), 
                    '\nWith contributions from\n\n', header2)
            buf.insert_with_tags(buf.get_end_iter(), 
'Radice David, gentoo bug #187595\n\
Christian Faulhammer, gentoo bug #192701\n')
            buf.insert_with_tags(buf.get_end_iter(), 
                    '\nDocumented by\n\n', header2)
            buf.insert_with_tags(buf.get_end_iter(), 
'Christian Faulhammer <opfer@gentoo.org>\n')
            buf.insert_with_tags(buf.get_end_iter(), 
                    '\nArtwork by\n\n', header2)
        else:
            buf = gtk.TextBuffer(self.texttagtable)
            for elog_section in self.selected_elog.contents(self.filter_list):
                buf.insert_with_tags(
                        buf.get_end_iter(),
                        elog_section.content,
                        buf.get_tag_table().lookup(elog_section.header))
        textview = self.gui.get_object("textview")
        textview.set_buffer(buf)

    def update_statusbar(self, idx=0):
		self.statusbar.push(0, self.message_statusbar(idx, len(self.model)))

    def main(self):
        gtk.main()

