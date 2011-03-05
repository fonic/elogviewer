#!/usr/bin/env python

# vi:ts=4 st=4 sw=4 et
# (c) 2010 Mathias Laurin, GPL2

'''
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
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
'''

class Identity:
	description = '''
<b>Elogviewer</b> lists all elogs created during emerges of packages from Portage, the package manager of the Gentoo linux distribution.  So all warnings or informational messages generated during an update can be reviewed at one glance.

Read
<tt>man 1 elogviewer</tt>
and
<tt>man 1 /etc/make.conf</tt>
for more information.
'''

class Filter:
    def __init__(self, label, match="", is_class=False, color='black'):
        self.name = label
        if match is "":
            self.match = label
        else:
            self.match = match
        self._is_class = is_class
        self.color = color
    
	def is_active(self):
		pass
    
    def is_class(self):
        return self._is_class
    

import os, fnmatch
def all_files(root, patterns='*', single_level=False, yield_folders=False):
    ''' Expand patterns for semicolon-separated strin of list '''
    patterns = patterns.split(';')
    for path, subdirs, files in os.walk(root):
        if yield_folders:
            files.extend(subdirs)
        files.sort()
        for name in files:
            for pattern in patterns:
                if fnmatch.fnmatch(name, pattern):
                    yield os.path.join(path, name)
                    break
        if single_level:
            break

class ElogContentPart:
	def __init__(self, complete_header):
		self.header = complete_header[0]
		self.section = complete_header[1]
		self.content = '%s (%s)\n' % (self.header, self.section)

	def add_content(self, content):
		self.content = ''.join([self.content, content, '\n'])

import time
class Elog:
    def __init__(self, filename, elog_dir):
		self.filename = filename

		basename = os.path.basename(filename)
		split_filename = basename.split(":")
		if len(split_filename) is 3:
			(self.category, self.package, date) = split_filename
		if len(split_filename) is 2:
			self.category = os.path.dirname(filename).split("/")[-1]
			(self.package, date) = split_filename
		date = time.strptime(date, "%Y%m%d-%H%M%S.log")
		self.sorted_time = time.strftime("%Y-%m-%d %H:%M:%S", date)
		self.locale_time = time.strftime("%x %X", date)

	def contents(self, filter_list):
		'''Parse file'''
		file_object = open(self.filename, 'r')
		try:
			lines = file_object.read().splitlines()
		finally:
			file_object.close()
		now = -1
		elog_content = []
		for line in lines:
			L = line.split(': ')
			if len(L) is 2 and (L[0] and L[1]) in filter_list.keys():
				now += 1
				elog_content.append(ElogContentPart(L))
			elif filter_list[elog_content[now].header].is_active() and filter_list[elog_content[now].section].is_active():
				elog_content[now].add_content(line)
		return elog_content
        
    def delete(self):
		os.remove(self.filename)

class Elogviewer:

	def __init__(self):
		self.selected_elog = None
		self.filter_list = {}

	def add_filter(self, filter):
		self.filter_list[filter.match] = filter
	
	def populate(self):
		for file in all_files(self.cmdline_args.elog_dir, '*:*.log', False, True):
            self.model.EVappend(Elog(file, self.cmdline_args.elog_dir))
	
	def message_statusbar(self, idx, model_size):
		return "%i of %i\t%s" % (idx, model_size, 
				"no selection" if self.selected_elog is None else self.selected_elog.package)


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
class CommandLineArguments:
	def __init__(self, argv):
		# default arguments
		self.debug = False
		self.elog_dir = portage.settings["PORT_LOGDIR"]
		if self.elog_dir is "":
			self.elog_dir = "/var/log/portage"
		self.gui_frontend = "GTK" # GTK or QT

		# parse commandline
		try:
			opts, args = getopt.getopt(argv, 
					"dhgqp:", ["debug", "help", "gtk", "qt", "elogpath"])
		except getopt.GetoptError:
			help()
			usage()
			exit(1)
		for opt, arg in opts:
			if opt in ("-d", "--debug"):
				self.debug = True
				print "debug mode is set"
			elif opt in ("-q", "--qt"):
				self.gui_frontend = "QT"
			elif opt in ("-h", "--help"):
				help()
				usage()
				exit (0)
			elif opt in ("-p", "--elogpath"):
				self.elog_dir = arg

		# post process arguments
		elog_dir = "/".join([self.elog_dir, "elog", ""])
		if os.path.isdir(elog_dir): 
			self.elog_dir = elog_dir

