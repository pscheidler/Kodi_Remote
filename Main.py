from PyQt5 import QtCore
from PyQt5 import QtGui
import PyQt5.QtWidgets as qtw
import queue
import MediaLibrary
import PlaylistTable
import PlaylistScanner
import FileScanner
import PickleHandler
import os
import shutil
import Settings
from Ui_MainWindow import Ui_MainWindow

#Base_Dir = "C:\\Users\\pscheidler\\Documents\\Work\\Xbmc Remote\\BetaUi\\"
#Base_Dir = "C:\\Users\\Janel\\Documents\\XBMC_Control\\"

class MyMainWindow(qtw.QMainWindow):
    def __init__(self, *args, **kwds):
        super().__init__()
#        QtGui.QMainWindow.__init__(self, *args, **kwds)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.Base_Dir = os.path.dirname(os.path.realpath(__file__))
#        wid = loadUi(os.path.join(self.Base_Dir, "Main.ui"), self)
        self.local_table_model = MediaLibrary.MediaLibrary(self, [])
        self.remote_table_model = MediaLibrary.MediaLibrary(self, [])
        self.left_playlist_table = PlaylistTable.PlaylistTable(self, [])
        self.right_playlist_table = PlaylistTable.PlaylistTable(self, [])
        self.ui.LocalTableL.setModel(self.local_table_model)
        self.ui.LocalTableR.setModel(self.local_table_model)
        self.ui.RemoteTableL.setModel(self.remote_table_model)
        self.ui.RemoteTableR.setModel(self.remote_table_model)
        self.ui.LeftPlaylistTable.setModel(self.left_playlist_table)
        self.ui.RightPlaylistTable.setModel(self.right_playlist_table)
        self.ui.LocalTableL.setSortingEnabled(True)
        self.ui.LocalTableR.setSortingEnabled(True)
        self.ui.RemoteTableL.setSortingEnabled(True)
        self.ui.RemoteTableR.setSortingEnabled(True)
        self.ui.RightPlaylistTable.setSortingEnabled(True)
        self.ui.LeftPlaylistTable.setSortingEnabled(True)
        self.AlbumList = {}
        self.sendQueue = queue.Queue()
        self.Id = 1
        self.local_server = None
        self.local_server_thread = None
        self.remote_server = None
        self.remote_server_thread = None
        self.menu = qtw.QMenu(self)
        copy_action = qtw.QAction('Copy File', self)
        copy_action.triggered.connect(self.copy_file)
        self.menu.addAction(copy_action)
        add_action = qtw.QAction('Add to Playlist', self)
        add_action.triggered.connect(self.add_to_playlist)
        self.menu.addAction(add_action)
        self.playlistMenu = qtw.QMenu(self)
        delete_action = qtw.QAction('Remove File', self)
        delete_action.triggered.connect(self.delete_file)
        self.menu.addAction(delete_action)
        self.context_table = None
        self.present_dest = None
        PickleHandler.PickleReader(self.Base_Dir, self.local_table_model, self.remote_table_model)

#    @QtCore.Slot()
    def local_edit_dirs(self):
        self.edit_dirs(local=True)

#    @QtCore.Slot()
    def remote_edit_dirs(self):
        self.edit_dirs(local=False)

#    @QtCore.Slot()
    def left_save_remote(self):
        self.save_playlist(self.left_playlist_table, local=False)

#    @QtCore.Slot()
    def left_save_local(self):
        self.save_playlist(self.left_playlist_table, local=True)

#    @QtCore.Slot()
    def right_save_remote(self):
        self.save_playlist(self.right_playlist_table, local=False)

#    @QtCore.Slot()
    def right_save_local(self):
        self.save_playlist(self.right_playlist_table, local=True)

    def save_playlist(self, playlist_table, local=True):
        if not local:
            start_dir = Settings.Remote_Playlist_Dir
        else:
            start_dir = ''
        save_file = str(QtGui.QFileDialog.getSaveFileName(self, "Save Playlist As", start_dir,
                                                          "MP3 Playlist (*.m3u)")[0])
        log = playlist_table.save(save_file, local=local)
        display_msg = ""
        if log["none"]:
            display_msg = "The following files had no match:\n"
            for x in log["none"]:
                display_msg += "%s\n" % x
        if log["close"]:
            display_msg += "The following files are inexact matches:\n"
            for x in log["close"]:
                display_msg += "%s matched with %s\n" % (x[0], x[1])
        if display_msg:
            print(display_msg)

#    @QtCore.Slot(QtCore.QPoint)
    def left_local_context(self, QPoint):
        self.context_table = self.ui.LocalTableL
        self.present_dest = "Xbmc"
        self.menu.popup(QtGui.QCursor.pos())

#    @QtCore.Slot(QtCore.QPoint)
    def right_local_context(self, QPoint):
        self.context_table = self.ui.LocalTableR
        self.present_dest = "Xbmc"
        self.menu.popup(QtGui.QCursor.pos())

#    @QtCore.Slot(QtCore.QPoint)
    def left_remote_context(self, QPoint):
        self.context_table = self.ui.RemoteTableL
        self.present_dest = "Local"
        self.menu.popup(QtGui.QCursor.pos())

#    @QtCore.Slot(QtCore.QPoint)
    def right_remote_context(self, QPoint):
        self.context_table = self.ui.RemoteTableR
        self.present_dest = "Local"
        self.menu.popup(QtGui.QCursor.pos())

    def copy_file(self):
        print("Called Copy Action!")
        rows = self.context_table.selectionModel().selectedRows()
        if self.present_dest == "Xbmc":
            table_list = self.local_table_model.my_list
            target_dir = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory", Settings.Remote_Music_Dir))
        else:
            table_list = self.remote_table_model.my_list
            target_dir = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory", ''))
        if not target_dir:
            print("Skipping copy")
            return
        files = []
        for row in rows:
            source_file = table_list[row.row()]['file']
            target_file = os.path.join(target_dir, os.path.basename(source_file))
            files.append([source_file, target_file])
        print("Starting copy, this could take a sec")
        for file in files:
            if os.path.isfile(file[1]):
                print("File already exists at %s, skipping copy" % file[1])
                continue
            shutil.copy(file[0], file[1])
        #print(files)

    def add_to_playlist(self):
        print("Add Action Called!")
        model = self.context_table.selectionModel()
        rows = model.selectedRows()
        table_list = self.remote_table_model.my_list
        # target_dir = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory", ''))
        files = []
        songList = [table_list[row.row()] for row in rows]
        self.right_playlist_table.insertRows(songList)
        for row in rows:
            source_file = table_list[row.row()]['file']
            print(source_file)
            # files.append([source_file, target_file])
        print("Files selected %s" % (files))

    def edit_dirs(self, local=True):
        if local:
            dirs = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory"))
        else:
            dirs = Settings.Remote_Music_Dir
        #print("Dirs = %s" % dirs)
        if local:
            table = self.local_table_model
        else:
            table = self.remote_table_model
        MyMainWindow.scan_dir_to_table(table, dirs)
        print("Started")
        return

    @staticmethod
    def scan_dir_to_table(table, my_dir, ignore_files=()):
        print("Starting scan of %s" % (my_dir.encode()))
        table.server = FileScanner.LocalFileScanner(table.file_queue, ignore_files=ignore_files)
        table.server_thread = QtCore.QThread()
        table.server.set_params(my_dir, subdirs=True)
        table.server.moveToThread(table.server_thread)
        table.server.signal.connect(table.rows_from_server)
        table.server_thread.started.connect(table.server.run)
        table.server_thread.start()

#    @QtCore.Slot()
    def sync_files(self):
        self.local_table_model.sync_prep()
        self.remote_table_model.sync_prep()
        self.local_table_model.sync_to(self.remote_table_model)
        self.remote_table_model.sync_to(self.local_table_model)

#    @QtCore.Slot()
    def remote_quick_refresh(self):
        MyMainWindow.refresh(self.remote_table_model, ignore_files=self.remote_table_model.get_all_files())

#    @QtCore.Slot()
    def local_quick_refresh(self):
        MyMainWindow.refresh(self.local_table_model, ignore_files=self.local_table_model.get_all_files())

#    @QtCore.Slot()
    def local_full_refresh(self):
        MyMainWindow.refresh(self.local_table_model)

#    @QtCore.Slot()
    def remote_full_refresh(self):
        MyMainWindow.refresh(self.remote_table_model)

    def delete_file(self):
        pass

    @staticmethod
    def refresh(table, ignore_files=()):
        if len(ignore_files) == 0:
            table.clear_all_rows()
#        for my_dir in table.get_root_dirs():
        MyMainWindow.scan_dir_to_table(table, my_dir, ignore_files=ignore_files)

#    @QtCore.Slot()
    def left_load_playlist(self):
        self.load_playlist(self.left_playlist_table)

#    @QtCore.Slot()
    def right_load_playlist(self):
        self.load_playlist(self.right_playlist_table)

    def load_playlist(self, list_table):
        file = str(QtGui.QFileDialog.getOpenFileName(self, 'Select Playlist', self.Base_Dir, #
                                                     'Playlists (*.m3u *.xspf);;All files (*.*)')[0])
        print("Playlist = %s" % file)
        if not os.path.isfile(file):
            print("no such file")
            return
        scanner = PlaylistScanner.PlaylistScanner(self.local_table_model, self.remote_table_model, list_table)
        scanner.run(file)

    def send_req(self, method, params=None):
        Req = {"jsonrpc": "2.0", "id": "%s!%d" % (method, self.Id), "method": method}
        if params:
            Req["params"] = params
        self.sendQueue.put(Req)
        self.Id += 1

    def on_close(self):
        PickleHandler.PickleWriter(self.Base_Dir, self.local_table_model, self.remote_table_model)
        self.local_table_model.close()
        self.remote_table_model.close()

    def closeEvent(self, *args, **kwargs):
        self.on_close()
        return QtGui.QMainWindow.closeEvent(self, *args, **kwargs)

    @staticmethod
    def get_bad_syncs(table):
        close_list = []
        alone_list = []
        for x in table.my_list:
            if x['sync state'] == "close":
                close_list.append(x)
            elif x['sync state'] == "alone":
                alone_list.append(x)
        return close_list, alone_list

if __name__ == "__main__":
    import sys
    app = qtw.QApplication(sys.argv)
    MainWindow = MyMainWindow()
    MainWindow.show()
    sys.exit(app.exec_())
