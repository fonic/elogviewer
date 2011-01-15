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

import libelogviewer.core as ev
 
( ELOG, CATEGORY, PACKAGE, TIMESTAMP, TIMESORT, FILENAME ) = range(6)
from gobject import TYPE_STRING, TYPE_PYOBJECT
class ListStore(gtk.ListStore):
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

class Filter(ev.FilterCommon):
    def __init__(self, label, match="", is_class=False, color='black'):
        self.button = gtk.CheckButton(label)
        self.button.set_active(True)
		ev.FilterCommon.__init__(self, label, match, is_class, color)
    
    def is_active(self):
        return self.button.get_active()


class ElogviewerGtk(ev.ElogviewerCommon):

	def __init__(self, cmdline_args):
		ev.ElogviewerCommon.__init__(self)
		self.filter_counter_class = 0
		self.filter_counter_stage = 0
		self.filter_columns_class = 2
		self.filter_columns_stage = self.filter_columns_class 
		self.texttagtable = gtk.TextTagTable()
		self.cmdline_args = cmdline_args
    
    def create_gui(self):
		gladefile = '/'.join([path.split(__file__)[0], "elogviewer.glade"])
		self.gui = gtk.Builder()
		self.gui.add_from_file(gladefile)

		self.treeview = self.gui.get_object("treeview")
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
        if not self.cmdline_args.get_debug_status():
            sorted_time_col.set_visible(False)
            filename_col.set_visible(False)

        self.treeview.append_column(category_col)
        self.treeview.append_column(package_col)
        self.treeview.append_column(locale_time_col)
        self.treeview.append_column(sorted_time_col)
        self.treeview.append_column(filename_col)
        self.treeview.set_enable_search(False)
        #self.treeview.set_search_column(FILENAME)

		self.treeview.set_model(ListStore())

		self.textview = self.gui.get_object("textview")

		self.statusbar = self.gui.get_object("statusbar")
		self.statusbar.push(0, "0 of 0")
 
	def connect(self):
		self.gui.connect_signals({
			"on_window_destroy" : gtk.main_quit,
			"on_actionQuit_activate" : self.on_actionQuit,
			"on_actionDelete_activate" : self.on_actionDelete,
			"on_actionRefresh_activate" : self.on_actionRefresh,
			"on_actionAbout_activate" : self.on_actionAbout,
			"on_liststore_row_deleted": self.on_row_deleted
					})
        self.treeview.get_selection().connect('changed', self.on_selection_changed)

	def show(self):
		main_window = self.gui.get_object("window")
		main_window.show()

	def quit(self):
		gtk.main_quit()

    def add_filter(self, filter):
		ev.ElogviewerCommon.add_filter(self, filter)

		filter_class_table = self.gui.get_object("filter_class_table")
		filter_stage_table = self.gui.get_object("filter_stage_table")
        if filter.is_class():
            (t, l) = divmod(self.filter_counter_class, self.filter_columns_class)
            r = l + 1
            b = t + 1
            filter_class_table.attach(filter.button, l, r, t, b)
            self.filter_counter_class += 1
        else:
            (t, l) = divmod(self.filter_counter_stage, self.filter_columns_stage)
            r = l + 1
            b = t + 1
            filter_stage_table.attach(filter.button, l, r, t, b)
            self.filter_counter_stage += 1
		if filter.is_class():
			tag = gtk.TextTag(filter.match)
			tag.set_property('foreground', filter.color)
			self.texttagtable.add(tag)
        filter.button.connect('toggled', self.on_filter_btn)
        filter.button.show()

	def on_actionQuit(self, action):
		self.quit()
	
	def on_actionAbout(self, action):
		About(ev.ElogviewerIdentity())
	
    def on_actionDelete(self, model, path, iter):
        model.get_value(iter).delete()
        model.remove(iter)
    
    def on_actionRefresh(self, action):
		self.refresh()

	def refresh(self):
        selected_path = 0
        selection = self.treeview.get_selection()
        (model, iter) = selection.get_selected()
        if selection.count_selected_rows() is not 0:
            selected_path = model.get_path(iter)[0]
        model.clear()
        self.populate()
        if selected_path <= len(model):
            selection.select_path(selected_path)
        elif len(model) is not 0:
            selection.select_path(0)

    def on_filter_btn(self, widget):
        selection = self.treeview.get_selection()
        self.read_elog(selection)
    
    def on_selection_changed(self, selection):
        if selection.count_selected_rows() is not 0:
            (model, iter) = selection.get_selected()
            if not model.iter_has_child(iter):
                self.read_elog(selection)
        self.update_statusbar(selection)
    
    def on_row_deleted(self, model, path):
        selection = self.treeview.get_selection()
        path = path[0]
        if len(model) is not 0:
            if path is len(model):
                selection.select_path(path-1)
            else:
                selection.select_path(path)
    
    def read_elog(self, selection):
		buffer = gtk.TextBuffer(self.texttagtable)
        if selection.count_selected_rows() is not 0:
            (model, iter) = selection.get_selected()
			selected_elog = model.get_value(iter)
			for elog_section in selected_elog.contents(self.filter_list):
				(start_iter, end_iter) = buffer.get_bounds()
				buffer.insert_with_tags(
						end_iter,
						elog_section.content,
						buffer.get_tag_table().lookup(elog_section.header))

		self.textview.set_buffer(buffer)
        self.update_statusbar(selection)

    def update_statusbar(self, selection):
        selected_path = -1
        model_size = 0
        filename = ""
        if selection.count_selected_rows() is not 0:
            (model, iter) = selection.get_selected()
            selected_path = model.get_path(iter)[0]
            model_size = len(model)
            filename = model.get_value(iter).filename
        self.statusbar.push(0, 
            str(selected_path + 1)
            + ' of ' +
            str(model_size)
            + '\t' +
            filename)

	def populate(self):
        model = self.treeview.get_model()
        for file in ev.all_files(self.cmdline_args.get_elogdir(), '*:*.log', False, True):
            model.append(ev.Elog(file, self.cmdline_args.get_elogdir()))

    def main(self):
        gtk.main()

