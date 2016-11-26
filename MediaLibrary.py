__author__ = 'pscheidler'
from PyQt5 import QtCore
import operator
import os
import queue


class MediaLibrary(QtCore.QAbstractTableModel):
    column_names = ["title", "file", "album", "artist", "sync state", "partner"]
    item_features = {"title", "file", "album", "artist", "sync state", "genre", "year", "track", "length", "image",
                     "partner", "size"}
    search_key = "title"  # When syncing songs, mainly look for same title
    match_keys = ["album", "artist"]  # These must match for full match, otherwise it is partial

    def __init__(self, parent, mylist, *args):
        super().__init__(parent, *args)
        self.my_list = mylist
        # if len(self.my_list) == 0:
        #           self.my_list = [{x: "" for x in self.item_features}]
        self.file_queue = queue.Queue()
        self.dir_queue = queue.Queue()
        self.my_dirs = []
        self.root_dirs = []
#        self.server = None
#        self.server_thread = None

    def rowCount(self, parent):
        return len(self.my_list)

    def columnCount(self, parent):
        return len(self.column_names)

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        return self.my_list[index.row()][self.column_names[index.column()]]

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            if col > len(self.column_names):
                print("CAUGHT ERROR, COL %s" % col)
                return None
            return self.column_names[col]
        return None

    def sort(self, col, order):
        """sort table by given column number col"""
        self.layoutAboutToBeChanged.emit()
        try:
            self.my_list = sorted(self.my_list, key=operator.itemgetter(self.column_names[col]))
        except:
            print("Can't sort column %s" % col)
        if order == QtCore.Qt.DescendingOrder:
            self.my_list.reverse()
        self.layoutChanged.emit()

    def insertRows(self, data):
        rows = self.rowCount(None)
        print("1")
        self.beginInsertRows(QtCore.QModelIndex(), rows, rows + len(data) - 1)
        for x in data:
            print("2")
            if x == "Done":
                print("GOTDONE")
                continue
            for y in self.item_features:
                print("3, %s, %s" % (x, y))
                if y not in x:
                    x[y] = ""
            self.my_list.append(x)
        print("4")
        self.endInsertRows()
        print("5")
        return True

    def rows_from_server(self):
        row_list = []
        while not self.file_queue.empty():
            row_list.append(self.file_queue.get())
        self.insertRows(row_list)
        while not self.dir_queue.empty():
            my_dir = self.dir_queue.get()
            if my_dir not in self.my_dirs:
                self.my_dirs.append(my_dir)

    def sync_prep(self):
        for x in self.my_list:
            x["sync state"] = "unknown"

    def sync_to(self, model):
        for x in self.my_list:
            if x["sync state"] is "unknown":
                #print(x["title"])
                model.match_item(x)

    @staticmethod
    def set_good_match(a, b):
        a["partner"] = b["file"]
        b["partner"] = a["file"]
        a["sync state"] = "good"
        b["sync state"] = "good"

    @staticmethod
    def set_close_match(a, b):
        if not a["sync state"] == "good":
            a["sync state"] = "close"
            if not isinstance(a["partner"], list):
                a["partner"] = [b["file"]]
            else:
                a["partner"].append(b["file"])
        if not b["sync state"] == "good":
            b["sync state"] = "close"
            if not isinstance(b["partner"], list):
                b["partner"] = [a["file"]]
            else:
                b["partner"].append(a["file"])

    def run_partner_match(self, item, partner_file):
        my_item = self.get_file_info(partner_file)
        if my_item:
            match = self.match_songs(my_item, item)
            if match == "good":
                self.set_good_match(my_item, item)
                return True
            if match == "close":
                self.set_close_match(my_item, item)
            else:
                if isinstance(item["partner"], list):
                    item["partner"].remove(partner_file)
                else:
                    item["partner"] = None
        return False

    def match_item(self, item):
        #print(item["file"])
        if item["partner"]:
            if isinstance(item["partner"], str):
                if self.run_partner_match(item, item["partner"]):
                    return
            elif isinstance(item["partner"], list):
                for x in item["partner"]:
                    if self.run_partner_match(item, x):
                        return
        for x in self.my_list:
            match_result = self.match_songs(x, item)
            if match_result == "good":
                self.set_good_match(x, item)
                return True
            if match_result == "close":
                self.set_close_match(x, item)
        if item["sync state"] == "unknown":
            item["sync state"] = "alone"

    @staticmethod
    def match_songs(a, b):
        # Criteria 1: If the file name (excluding dir) and size match, then it is a match
        if os.path.basename(a['file']).lower == os.path.basename(b['file']).lower():
            if a['size'] == b['size']:
                return "good"
        # If the sizes are too far apart, there is no match
        if abs(a['size'] - b['size']) > 500000:
            return False
        # Otherwise, check the music parameters!
        if not a[MediaLibrary.search_key] == b[MediaLibrary.search_key]:
            return False
        for k in MediaLibrary.match_keys:
            if a[k] != b[k]:
                return "close"
        return "good"

    def close(self):
        pass
        # if self.server_thread:
        #     self.server_thread.terminate()

    def get_file_info(self, search_file):
        search_file = search_file.lower()
        for x in self.my_list:
            if x['file'].lower() == search_file:
                return x
        return None

    def get_song_info(self, criteria, min_matches=2):
        keylist = list(criteria.keys())
        len_keylist = len(keylist)
        if min_matches > len_keylist:
            min_matches = len_keylist
        suggestion_list = []
        for i, search_key in enumerate(keylist[:1 - min_matches]):
            for song in self.my_list:
                if song[search_key] == criteria[search_key]:
                    matches = 1
                    for key in keylist[i + 1:]:
                        if song[key] == criteria[key]:
                            matches += 1
                    if matches == len_keylist:
                        return song
                    if matches >= min_matches:
                        suggestion_list.append(song)
        if not suggestion_list:
            return None
        return suggestion_list[0]

    def get_new_files(self, files):
        return_list = []
        for x in files:
            if x not in (y["file"] for y in self.my_list):
                return_list.append(x)

    def get_all_files(self):
        return [y["file"] for y in self.my_list]

    def get_contents(self):
        return self.my_list

    def set_contents(self, data):
        self.insertRows(data)

    def get_dirs(self):
        return self.my_dirs

    def add_root_dirs(self, new_dir):
        if type(new_dir) is list:
            return_value = False
            for x in new_dir:
                return_value = return_value or self._add_root_dir(x)
        else:
            return_value = self._add_root_dir(new_dir)
        self.clean_root_dir_list()
        return return_value

    def _add_root_dir(self, new_dir):
        new_dir = os.path.join(new_dir, '').upper()
        if new_dir not in self.root_dirs:
            self.root_dirs.append(new_dir)
            return True
        return False

    def get_root_dirs(self):
        return self.root_dirs

    def clean_root_dir_list(self):
        delete_list = []
        for (ix, x) in enumerate(self.root_dirs):
            for (iy, y) in enumerate(self.root_dirs):
                if ix == iy: continue
                if x in y:
                    if iy not in delete_list:
                        delete_list.append(iy)
        new_list = []
        for (ix, x) in enumerate(self.root_dirs):
            if ix not in delete_list:
                new_list.append(x)
        self.root_dirs = new_list

    def clear_all_rows(self):
        self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self.my_list))
        self.my_list = []
        self.endRemoveRows()
