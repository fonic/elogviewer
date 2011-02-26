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

import libelogviewer.core as core
 
( ELOG, CATEGORY, PACKAGE, TIMESTAMP, TIMESORT, FILENAME ) = range(6)
from gobject import TYPE_STRING, TYPE_PYOBJECT
class Model(gtk.ListStore):
    def __init__(self):
        gtk.ListStore.__init__(self,
            TYPE_PYOBJECT, TYPE_STRING, TYPE_STRING, TYPE_STRING, TYPE_STRING, TYPE_STRING )
    
    def append(self, elog):
        return gtk.ListStore.append(self, [elog, elog.category, elog.package,
            elog.locale_time, elog.sorted_time, elog.filename])
    
    def get_value(self, iter):
        return gtk.ListStore.get_value(self, iter, 0)

class About(gtk.AboutDialog):
    def __init__(self, identity):
        gtk.AboutDialog.__init__(self)
        self.set_version(identity.version)
        self.set_website(identity.website)
        self.set_authors(identity.author)
        self.set_artists(identity.artists)
        self.set_copyright(identity.copyright)
        self.set_documenters(identity.documenter)
        self.set_license(identity.LICENSE)
        self.run()
        self.destroy()

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

        self.filter_counter_class = self.filter_counter_stage = 0
        self.filter_columns_class = self.filter_columns_stage = 2
    
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
        #self.treeview.set_search_column(FILENAME)

        self.statusbar = self.gui.get_object("statusbar")

    def connect(self):
        self.gui.connect_signals({
            "on_window_destroy" : gtk.main_quit,
            "on_actionQuit_activate" : gtk.main_quit,
            "on_actionDelete_activate" : self.on_actionDelete,
            "on_actionRefresh_activate" : self.on_actionRefresh,
            "on_actionAbout_activate" : self.on_actionAbout,
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

    def on_actionAbout(self, action):
        About(core.Identity())
    
    def show(self):
        main_window = self.gui.get_object("window")
        main_window.show()
        self.populate()
        self.update_statusbar()

    def refresh(self):
        self.model.clear()
        self.populate()

    def populate(self):
        for file in core.all_files(self.cmdline_args.elog_dir, '*:*.log', False, True):
            self.model.append(core.Elog(file, self.cmdline_args.elog_dir))

    def add_filter(self, filter):
        filter.button.connect('toggled', self.read_elog)
        core.Elogviewer.add_filter(self, filter)

        filter_class_table = self.gui.get_object("filter_class_table")
        filter_stage_table = self.gui.get_object("filter_stage_table")
        if filter.is_class():
            (t, l) = divmod(self.filter_counter_class, self.filter_columns_class)
            filter_class_table.attach(filter.button, l, l+1, t, t+1)
            self.filter_counter_class += 1
        else:
            (t, l) = divmod(self.filter_counter_stage, self.filter_columns_stage)
            filter_stage_table.attach(filter.button, l, l+1, t, t+1)
            self.filter_counter_stage += 1
        if filter.is_class():
            tag = gtk.TextTag(filter.match)
            tag.set_property('foreground', filter.color)
            self.texttagtable.add(tag)
        filter.button.show()

    def read_elog(self):
        textview = self.gui.get_object("textview")
        if self.selected_elog is None:
            textview.get_buffer().set_text("")
            return
        buffer = gtk.TextBuffer(self.texttagtable)
        for elog_section in self.selected_elog.contents(self.filter_list):
            (start_iter, end_iter) = buffer.get_bounds()
            buffer.insert_with_tags(
                    end_iter,
                    elog_section.content,
                    buffer.get_tag_table().lookup(elog_section.header))
        textview.set_buffer(buffer)

    def update_statusbar(self, idx=0):
        if self.selected_elog is None:
            filename = "no selection"
        else:
            filename = self.selected_elog.package
        model_size = len(self.model)
        message = "%i of %i\t%s" % (idx, model_size, filename)
        self.statusbar.push(0, message)

    def main(self):
        gtk.main()

