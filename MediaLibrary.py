__author__ = 'pscheidler'
from PyQt5 import QtCore
import operator
import os
import queue
from MainSongList import MainSongList


class MediaLibrary(QtCore.QAbstractTableModel):
    column_names = ["title", "album", "artist", "local count", "remote count"]

    def __init__(self, parent, mylist, *args):
        super().__init__(parent, *args)
        self.song_list = MainSongList(mylist=mylist)
        self.file_queue = queue.Queue()

    def rowCount(self, parent):
        return len(self.song_list.song_list)

    def columnCount(self, parent):
        return len(self.column_names)

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        return self.song_list.song_list[index.row()][self.column_names[index.column()]]

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
            self.song_list.song_list = sorted(self.song_list.song_list, key=operator.itemgetter(self.column_names[col]))
        except:
            print("Can't sort column %s" % col)
        if order == QtCore.Qt.DescendingOrder:
            self.song_list.song_list.reverse()
        self.layoutChanged.emit()

    # this now expects correctly formatted data!
    def insertRows(self, data):
        rows = self.rowCount(None)
        new_rows, data = self.song_list.prep_songs(data)
        self.beginInsertRows(QtCore.QModelIndex(), rows, rows + new_rows - 1)
        self.song_list.add_songs(data)
        self.endInsertRows()
        return True

    def rows_from_server(self):
        """ rows_from_server is called by an emit, pulls data out of the file queue, and adds it into the row list """
        row_list = []
        while not self.file_queue.empty():
            new_row = self.file_queue.get()
            if new_row != "Done":
                row_list.append(self.file_queue.get())
        self.insertRows(row_list)

    def close(self):
        pass
        # if self.server_thread:
        #     self.server_thread.terminate()

    # def get_file_info(self, search_file):
    #     search_file = search_file.lower()
    #     for x in self.my_list:
    #         if x['file'].lower() == search_file:
    #             return x
    #     return None

    # def get_song_info(self, criteria, min_matches=2):
    #     keylist = list(criteria.keys())
    #     len_keylist = len(keylist)
    #     if min_matches > len_keylist:
    #         min_matches = len_keylist
    #     suggestion_list = []
    #     for i, search_key in enumerate(keylist[:1 - min_matches]):
    #         for song in self.my_list:
    #             if song[search_key] == criteria[search_key]:
    #                 matches = 1
    #                 for key in keylist[i + 1:]:
    #                     if song[key] == criteria[key]:
    #                         matches += 1
    #                 if matches == len_keylist:
    #                     return song
    #                 if matches >= min_matches:
    #                     suggestion_list.append(song)
    #     if not suggestion_list:
    #         return None
    #     return suggestion_list[0]

    def get_all_files(self):
        return self.song_list.get_all_files()

    def get_contents(self):
        return self.song_list.song_list

    def set_contents(self, data):
        self.insertRows(data)

    def clear_all_rows(self):
        self.beginRemoveRows(QtCore.QModelIndex(), 0, len(self.song_list.song_list))
        self.song_list.clear_display()
        self.endRemoveRows()

# def sync_prep(self):
#     for x in self.my_list:
#         x["sync state"] = "unknown"
#
# def sync_to(self, model):
#     for x in self.my_list:
#         if x["sync state"] is "unknown":
#             #print(x["title"])
#             model.match_item(x)
#
# @staticmethod
# def set_good_match(a, b):
#     a["partner"] = b["file"]
#     b["partner"] = a["file"]
#     a["sync state"] = "good"
#     b["sync state"] = "good"
#
# @staticmethod
# def set_close_match(a, b):
#     if not a["sync state"] == "good":
#         a["sync state"] = "close"
#         if not isinstance(a["partner"], list):
#             a["partner"] = [b["file"]]
#         else:
#             a["partner"].append(b["file"])
#     if not b["sync state"] == "good":
#         b["sync state"] = "close"
#         if not isinstance(b["partner"], list):
#             b["partner"] = [a["file"]]
#         else:
#             b["partner"].append(a["file"])
#
# def run_partner_match(self, item, partner_file):
#     my_item = self.get_file_info(partner_file)
#     if my_item:
#         match = self.match_songs(my_item, item)
#         if match == "good":
#             self.set_good_match(my_item, item)
#             return True
#         if match == "close":
#             self.set_close_match(my_item, item)
#         else:
#             if isinstance(item["partner"], list):
#                 item["partner"].remove(partner_file)
#             else:
#                 item["partner"] = None
#     return False
#
# def match_item(self, item):
#     #print(item["file"])
#     if item["partner"]:
#         if isinstance(item["partner"], str):
#             if self.run_partner_match(item, item["partner"]):
#                 return
#         elif isinstance(item["partner"], list):
#             for x in item["partner"]:
#                 if self.run_partner_match(item, x):
#                     return
#     for x in self.my_list:
#         match_result = self.match_songs(x, item)
#         if match_result == "good":
#             self.set_good_match(x, item)
#             return True
#         if match_result == "close":
#             self.set_close_match(x, item)
#     if item["sync state"] == "unknown":
#         item["sync state"] = "alone"

# @staticmethod
# def match_songs(a, b):
#     # Criteria 1: If the file name (excluding dir) and size match, then it is a match
#     if os.path.basename(a['file']).lower == os.path.basename(b['file']).lower():
#         if a['size'] == b['size']:
#             return "good"
#     # If the sizes are too far apart, there is no match
#     if abs(a['size'] - b['size']) > 500000:
#         return False
#     # Otherwise, check the music parameters!
#     if not a[MediaLibrary.search_key] == b[MediaLibrary.search_key]:
#         return False
#     for k in MediaLibrary.match_keys:
#         if a[k] != b[k]:
#             return "close"
#     return "good"
#
