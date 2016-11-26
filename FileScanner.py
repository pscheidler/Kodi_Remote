__author__ = 'pscheidler'
from PyQt5 import QtCore
import queue
from MediaTranslate import MediaTranslate
import os
import time


class FileScanner(QtCore.QObject):
    update_interval = 0.1

    def __init__(self, file_queue, dir_queue, ignore=(), ignore_files=()):
        self.recv_queue = queue.Queue()
        self.file_queue = file_queue
        self.dir_queue = dir_queue
        super().__init__()
        self.my_dirs = ignore[:]
        self.ignore_files = ignore_files[:]
        # print(self.ignore_files)
        self.timer = 0
        self.dir_name = ""
        self.subdirs = False
        self.sync_state = None

    def clear_dirs(self, which=None):
        if not which:
            self.my_dirs = []
            return
        self.my_dirs = [x for x in self.my_dirs if x not in which]

    def send_dirs(self, dir_name, my_files=None, sync_state=None):
        if not my_files:
            my_files = os.listdir(dir_name)
        print(my_files)
        for fn in my_files:
            full_name = os.path.join(dir_name, fn)
            print(full_name)
            if full_name in self.ignore_files:
                self.ignore_files.remove(full_name)
                continue
            file_info = MediaTranslate.get_info(full_name)
            if file_info:
                if sync_state:
                    file_info["sync state"] = sync_state
                self.send_file(file_info)

    def set_params(self, dir_name, subdirs=False, sync_state=None):
        self.dir_name = dir_name
        self.subdirs = subdirs
        self.sync_state = sync_state

#    def add_dirs(self):
    def run(self):
        dir_name = self.dir_name
        subdirs = self.subdirs
        sync_state = self.sync_state
        if not subdirs:
            self.dir_queue.put(dir_name)
            self.send_dirs(dir_name, sync_state=sync_state)
            print("Done 1")
            self.process_done()
            print("Done 2")
            return
        walker = os.walk(dir_name)
        for d, s, f in walker:
            print("Dir %s" % d.encode())
            if d not in self.my_dirs:
                self.dir_queue.put(d)
                self.send_dirs(d, my_files=f, sync_state="unknown")
        self.process_done()

    def send_file(self, row_info):
        self.file_queue.put(row_info)
        if time.clock() - self.timer > self.update_interval:
            self.timer = time.clock()
            return True
        return False

    def process_done(self):
        self.file_queue.put("Done")


class LocalFileScanner(FileScanner):
    signal = QtCore.pyqtSignal()

    def __init__(self, file_queue, dir_queue, ignore=(), ignore_files=()):
        super().__init__(file_queue, dir_queue, ignore=ignore, ignore_files=ignore_files)

    def send_file(self, row_info):
        if FileScanner.send_file(self, row_info):
            self.signal.emit()

    def process_done(self):
        FileScanner.process_done(self)
        self.signal.emit()


class RemoteFileScanner(FileScanner):
    signal = QtCore.pyqtSignal()

    def __init__(self, file_queue, dir_queue, ignore=()):
        super().__init__(file_queue, dir_queue, ignore=ignore)

    def send_file(self, row_info):
        if FileScanner.send_file(self, row_info):
            self.signal.emit()

    def process_done(self):
        FileScanner.process_done(self)
        self.signal.emit()
