#!/usr/bin/env python

# vi:ts=4 st=4 sw=4 et

class FilterCommon:
    def __init__(self, label, match="", is_class=False, color='black'):
        self._name = label
        if match is "":
            self._match = label
        else:
            self._match = match
        self._is_class = is_class
        self._color = color
        self._button.set_active(True)
    
	def is_active(self):
		pass
    
    def name(self):
        return self._name
    
    def match(self):
        return self._match

    def button(self):
		pass
        
    def is_class(self):
        return self._is_class
    
    def color(self):
        return self._color


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


import time
class Elog:
    def __init__(self, filename):
        itime = '%Y%m%d-%H%M%S.log'
        # see modules time and locale
        locale_time_fmt = '%x %X'
        sorted_time_fmt = '%Y-%m-%d %H:%M:%S'

        split_filename = filename[2:]
        split_filename = split_filename.split(':')
        t = self._category = self._package = ""
        if len(split_filename) is 3:
            (self._category, self._package, t) = split_filename
        elif len(split_filename) is 2:
            print split_filename
            (self._category, self._package) = split_filename[0].split('/')
            t = split_filename[1]
        t = time.strptime(t, itime)
        self._sorted_time = time.strftime(sorted_time_fmt, t)
        self._locale_time = time.strftime(locale_time_fmt, t)
        
        self._filename = filename
        
    def category(self):
        return self._category
        
    def package(self):
        return self._package
            
    def locale_time(self):
        return self._locale_time
        
    def sorted_time(self):
        return self._sorted_time
        
    def filename(self):
        return self._filename
        
    def delete(self):
        if not _debug:
            os.remove(self._filename)
        else:
            print self._filename
        return self

