#!/usr/bin/env python

# vi:ts=4 st=4 sw=4 et

_debug = False

_author     = ['Mathias Laurin <mathias_laurin@users.sourceforge.net>',
        'Timothy Kilbourn', 'Jeremy Wickersheimer',
        '',
        'contribution by',
        'Radice David, gentoo bug #187595',
        'Christian Faulhammer, gentoo bug #192701',]
_documenter = ['Christian Faulhammer <opfer@gentoo.org>']
_artists    = ['elogviewer needs a logo, artists are welcome to\ncontribute, please contact the author.']
_appname_    = 'elogviewer'
_version    = '0.6.2'
_website    = 'http://sourceforge.net/projects/elogviewer'
_copyright  = 'Copyright (c) 2007, 2010 Mathias Laurin'
_license    = 'GNU General Public License (GPL) version 2'


_LICENSE    = _copyright + '''

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.'''


_description = '''
<b>Elogviewer</b> lists all elogs created during emerges of packages from Portage, the package manager of the Gentoo linux distribution.  So all warnings or informational messages generated during an update can be reviewed at one glance.

Read
<tt>man 1 elogviewer</tt>
and
<tt>man 1 /etc/make.conf</tt>
for more information.

Timothy Kilbourn (nmbrthry) has written the first version of elogviewer.
Jeremy Wickersheimer adapted elogviewer to KDE, some features he added are now imported in elogviewer.
Christian Faulhammer (V-Li) has written the man page.
'''

# Redirect messages to stderr
import sys
sys.stdout = sys.stderr

try:
    import gtk
	import gtk.glade
except:
    print "a recent version of pygtk is required"
 
class CheckButton(gtk.CheckButton):
    def __init__(self, label, use_underline=False):
        gtk.CheckButton.__init__(self, label, use_underline)
        self.set_active(True)


class ElogTextBuffer(gtk.TextBuffer):

    filters = {}

    def __init__(self):
        gtk.TextBuffer.__init__(self)
    
    def create_tag(self, filter):
        if filter.is_class():
            gtk.TextBuffer.create_tag(self, 
                filter.match(), foreground=filter.color())
        self.filters[filter.match()] = filter

    def clear(self):
        self.delete(self.get_start_iter(), self.get_end_iter())

    def read(self, elog):
        self.clear()
        filename = elog.filename()
        if not filename:
            return
        file_obj = open(filename, 'r')
        try:
            # Parse file
            header = None
            section = None
            for line in file_obj.read().splitlines():
                L = line.split(': ')
                if len(L) is 2 and (L[0] and L[1]) in self.filters.keys():
                    (header, section) = L
                    self.insert_with_tags(
                        self.get_end_iter(),
                        header + ' (' + section + ')\n\n',
                        self.get_tag_table().lookup(header))
                elif self.filters[header].is_active() \
                    and self.filters[section].is_active():
                    self.insert_with_tags(
                        self.get_end_iter(),
                        line,
                        self.get_tag_table().lookup(header))
        finally:
            file_obj.close()


( ELOG, CATEGORY, PACKAGE, TIMESTAMP, TIMESORT, FILENAME ) = range(6)
from gobject import TYPE_STRING, TYPE_PYOBJECT
from elogviewerCommon import Elog, all_files
class ListStore(gtk.ListStore):
    def __init__(self):
        gtk.ListStore.__init__(self,
            TYPE_PYOBJECT, TYPE_STRING, TYPE_STRING, TYPE_STRING, TYPE_STRING, TYPE_STRING )
    
    def append(self, elog):
        return gtk.ListStore.append(self, [elog, elog.category(), elog.package(),
            elog.locale_time(), elog.sorted_time(), elog.filename()])
    
    def get_value(self, iter):
        return gtk.ListStore.get_value(self, iter, 0)

    def populate(self):
        for file in all_files(elog_dir, '*:*.log', False, True):
            self.append(Elog(file))

class About(gtk.AboutDialog):

    def __init__(self):
        gtk.AboutDialog.__init__(self)
        self.set_version( _version )
        self.set_website( _website )
        self.set_authors( _author )
        self.set_artists( _artists )
        self.set_copyright( _copyright )
        self.set_documenters( _documenter )
        self.set_license( _LICENSE )
        self.run()
        self.destroy()


class Info(gtk.MessageDialog):

    def __init__(self):
        gtk.MessageDialog.__init__(self, 
                parent=None, 
                #flasgs=0, 
                type=gtk.MESSAGE_INFO, 
                buttons=gtk.BUTTONS_OK, 
                message_format=None)
        self.set_markup ( _description )
        self.run()
        self.destroy()


import os
class ElogviewerGUI:

    def __init__(self):

        self.treeview = gtk.TreeView()
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
        if not _debug:
            sorted_time_col.set_visible(False)
            filename_col.set_visible(False)

        self.treeview.append_column(category_col)
        self.treeview.append_column(package_col)
        self.treeview.append_column(locale_time_col)
        self.treeview.append_column(sorted_time_col)
        self.treeview.append_column(filename_col)
        self.treeview.set_enable_search(False)
        #self.treeview.set_search_column(FILENAME)
        
        self.window.show_all()

        # connect
        model.connect('row_deleted', self.on_row_deleted)
        self.treeview.get_selection().connect('changed', self.on_selection_changed)

        self.statusbar.push(0, "0 of 0")
        self.statusbar.push(1, os.getcwd())
        self.refresh()


from elogviewerCommon import FilterCommon
class Filter(FilterCommon):
    def __init__(self, label, match="", is_class=False, color='black'):
        self._button = CheckButton(label, False)
        self._button.set_active(True)
		FilterCommon.__init__(self, label, match, is_class, color)
    
    def is_active(self):
        return self._button.get_active()

	def button(self):
		return self._button


class Elogviewer:

	def __init__(self):
		self.filter_counter_class = 0
		self.filter_counter_stage = 0
		self.filter_columns_class = 2
		self.filter_columns_stage = self.filter_columns_class 
    
	def quit(self):
		gtk.main_quit()

    def create_gui(self):
		self.gui = gtk.Builder()
		self.gui.add_from_file("elogviewer.glade")
	
	def connect(self):
		self.gui.connect_signals({
			"on_window_destroy" : gtk.main_quit,
			"on_actionQuit_activate" : self.on_actionQuit,
			"on_actionDelete_activate" : self.on_actionDelete,
			"on_actionRefresh_activate" : self.on_actionRefresh,
			"on_actionAbout_activate" : self.on_actionAbout
					})

	def show(self):
		main_window = self.gui.get_object("window")
		main_window.show()

    def add_filter(self, filter):
		filter_class_table = self.gui.get_object("filter_class_table")
		filter_stage_table = self.gui.get_object("filter_stage_table")
        if filter.is_class():
            (t, l) = divmod(self.filter_counter_class, self.filter_columns_class)
            r = l + 1
            b = t + 1
            filter_class_table.attach(filter.button(), l, r, t, b)
            self.filter_counter_class += 1
        else:
            (t, l) = divmod(self.filter_counter_stage, self.filter_columns_stage)
            r = l + 1
            b = t + 1
            filter_stage_table.attach(filter.button(), l, r, t, b)
            self.filter_counter_stage += 1
        #self.textview.get_buffer().create_tag(filter)
        filter.button().connect('toggled', self.on_filter_btn)
        filter.button().show()

	def on_actionQuit(self, action):
		self.quit()
	
	def on_actionAbout(self, action):
		pass
	
    def on_actionDelete(self, model, path, iter):
        model.get_value(iter).delete()
        model.remove(iter)
    
    def on_actionRefresh(self, action):
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

	def on_liststore_row_deleted(self, sth):
		print sth
	
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
        if selection.count_selected_rows() is not 0:
            (model, iter) = selection.get_selected()
            self.textview.get_buffer().read(model.get_value(iter))
        else:
            self.textview.get_buffer().clear()
        self.update_statusbar(selection)

    def update_statusbar(self, selection):
        selected_path = -1
        model_size = 0
        filename = ""
        if selection.count_selected_rows() is not 0:
            (model, iter) = selection.get_selected()
            selected_path = model.get_path(iter)[0]
            model_size = len(model)
            filename = model.get_value(iter).filename()
        self.statusbar.push(0, 
            str(selected_path + 1)
            + ' of ' +
            str(model_size)
            + '\t' +
            filename)

    def populate(self):
        model = self.treeview.get_model()
        model.populate()

    def main(self):
        gtk.main()
	

def help():
    print '''
Elogviewer should help you not to miss important information like: 

If you have just upgraded from an older version of python you
will need to run:
    /usr/sbin/python-updater

please do run it and restart elogviewer.
'''

def usage():
    print '''
You need to enable the elog feature by setting at least one of 
    PORTAGE_ELOG_CLASSES="info warn error log qa"
and
    PORTAGE_ELOG_SYSTEM="save"
in /etc/make.conf

You need to add yourself to the portage group to use 
elogviewer without privileges.

Read /etc/make.conf.example for more information
'''
    

import getopt
import portage
def main(argv):
    try:
        opts, args = getopt.getopt(argv, "dh", ["debug", "help"])
    except getopt.GetoptError:
        help()
        usage()
        exit(1)
    for opt, arg in opts:
        if opt in ("-d", "--debug"):
            global _debug
            _debug = True
            print "debug mode is set"
        elif opt in ("-h", "--help"):
            help()
            usage()
            exit (0)
    
	global elog_dir
    if _debug:
		elog_dir = "elog/elog"
    else:
        logdir = portage.settings["PORT_LOGDIR"]
        if logdir is not "":
			elog_dir = logdir
        else:
			elog_dir = "/var/log/portage"
        try:
			elog_dir += "/elog"
        except:
            usage()
            exit(2)

	elogviewer = Elogviewer()
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
    elogviewer.main()


if __name__ == "__main__":
    main(sys.argv[1:])
