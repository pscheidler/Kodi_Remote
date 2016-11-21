__author__ = 'pscheidler'
from PyQt5 import QtCore
from MediaTranslate import MediaTranslate
from XspfReader import XspfReader
import os.path

class PlaylistScanner(QtCore.QObject):
    """
    This class is not yet intended to run in a separate thread, it will go through a playlist file and associate each
    item with data from the corresponding table
    """
    update_interval = 0.1

    def __init__(self, local_table, remote_table, my_table):
        QtCore.QObject.__init__(self)
        self.local_table = local_table
        self.remote_table = remote_table
        self.my_table = my_table
        self.rows_to_add = []

    def run(self, list_name):
        if os.path.splitext(list_name)[1] == '.xspf':
            file_list = XspfReader(list_name).get_file_list()
            for file_name in file_list:
                line_info = self.local_table.get_file_info(file_name)
                if line_info:
                    self.add_row(line_info)
                else:
                    print("Can't find %s" % file_name)
            self.send_rows()
        else:
            self.m3u_translate(list_name)

    def m3u_translate(self, list_name):
        with open(list_name, 'r') as f:
            lines = f.readlines()
        next_file = {}
        for line in lines:
            if '/' in line:
                check_table = self.remote_table
            else:
                check_table = self.local_table
            if line.startswith('#'):
                if line.startswith('#EXTINF:'):
                    this_line = line.replace('#EXTINF:', '').strip()
                    this_line = this_line.split(',')
                    next_file = {"length": int(this_line[0])}
                    this_line = this_line[1].split(' - ', 1)
                    next_file["title"] = this_line[1]
                    next_file["artist"] = this_line[0]
                continue
            this_file = MediaTranslate.local_name(line.strip())
            line_info = check_table.get_file_info(this_file)
            if not line_info:
                line_info = check_table.get_song_info(next_file)
            if line_info:
                self.add_row(line_info)
            else:
                next_file['file'] = this_file
                self.add_row(next_file)
        self.send_rows()

    def add_row(self, line_info):
        self.rows_to_add.append(line_info)
        if len(self.rows_to_add) > 100:
            self.send_rows()

    def send_rows(self):
        self.my_table.insertRows(self.rows_to_add)
        self.rows_to_add = []
