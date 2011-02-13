#!/usr/bin/env python

# vi:ts=4 st=4 sw=4 et
# (c) 2010 Mathias Laurin, GPL2

class Identity:
	author = ['Mathias Laurin <mathias_laurin@users.sourceforge.net>',
			'Timothy Kilbourn', 'Jeremy Wickersheimer',
			'',
			'contribution by',
			'Radice David, gentoo bug #187595',
			'Christian Faulhammer, gentoo bug #192701',]
	documenter = ['Christian Faulhammer <opfer@gentoo.org>']
	artists = ['elogviewer needs a logo, artists are welcome to\ncontribute, please contact the author.']
	appname = 'elogviewer'
	version = '0.7.0'
	website = 'http://sourceforge.net/projects/elogviewer'
	copyright = 'Copyright (c) 2007, 2011 Mathias Laurin'
	license = 'GNU General Public License (GPL) version 2'
	LICENSE = '''
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
	description = '''
<b>Elogviewer</b> lists all elogs created during emerges of packages from Portage, the package manager of the Gentoo linux distribution.  So all warnings or informational messages generated during an update can be reviewed at one glance.

Read
<tt>man 1 elogviewer</tt>
and
<tt>man 1 /etc/make.conf</tt>
for more information.

Timothy Kilbourn (nmbrthry) has written the first version of elogviewer.
Jeremy Wickersheimer adapted elogviewer to KDE.
Christian Faulhammer (V-Li) has written the man page.
'''

class FilterCommon:
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
        itime = '%Y%m%d-%H%M%S.log'
        # see modules time and locale
        locale_time_fmt = '%x %X'
        sorted_time_fmt = '%Y-%m-%d %H:%M:%S'
		
		split_filename = filename.split(elog_dir)[1].split(':')
        t = self.category = self.package = ""
        if len(split_filename) is 3:
            (self.category, self.package, t) = split_filename
        elif len(split_filename) is 2:
            (self.category, self.package) = split_filename[0].split('/')
            t = split_filename[1]
        t = time.strptime(t, itime)
        self.sorted_time = time.strftime(sorted_time_fmt, t)
        self.locale_time = time.strftime(locale_time_fmt, t)
        self.filename = filename
        
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
        if not _debug:
            os.remove(self.filename)
        else:
            print self.filename
        return self

class ElogviewerCommon:

	def __init__(self):
		self.filter_list = {}

	def create_gui(self):
		pass

	def connect(self):
		pass

	def show(self):
		pass

	def refresh(self):
		pass

	def main(self):
		pass

	def quit(self):
		pass

	def add_filter(self, filter):
		self.filter_list[filter.match] = filter


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
		self.debug = False
		self.elog_dir = "."
		''' string GTK or QT '''
		self.gui_frontend = "GTK"

		try:
			opts, args = getopt.getopt(argv, "dhgq", ["debug", "help", "gtk", "qt"])
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
		
		if self.debug:
			self.elog_dir = "./elog/elog/"
		else:
			logdir = portage.settings["PORT_LOGDIR"]
			if logdir is "":
				logdir = "/var/log/portage"
			self.elog_dir = logdir + "/elog/"
		# FIXME
		# test if directory exists, spit error if not
		#	usage()
		#   exit(2)

