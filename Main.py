from PySide import QtGui
from PySide import QtCore
import queue
import MediaLibrary
import PlaylistTable
import PlaylistScanner
from UiLoader import UiLoader
import FileScanner
import PickleHandler
import os
import shutil

#Base_Dir = "C:\\Users\\pscheidler\\Documents\\Work\\Xbmc Remote\\BetaUi\\"
#Base_Dir = "C:\\Users\\Janel\\Documents\\XBMC_Control\\"
Xbmc_Music = "\\\\192.168.1.135\\Music"
Xbmc_Playlist = '\\\\192.168.1.135\\Userdata\\playlists\\music'


def loadUi(uifile, baseinstance=None):
    """
    Dynamically load a user interface from the given ``uifile``.

    ``uifile`` is a string containing a file name of the UI file to load.

    If ``baseinstance`` is ``None``, the a new instance of the top-level widget
    will be created.  Otherwise, the user interface is created within the given
    ``baseinstance``.  In this case ``baseinstance`` must be an instance of the
    top-level widget class in the UI file to load, or a subclass thereof.  In
    other words, if you've created a ``QMainWindow`` interface in the designer,
    ``baseinstance`` must be a ``QMainWindow`` or a subclass thereof, too.  You
    cannot load a ``QMainWindow`` UI file with a plain
    :class:`~PySide.QtGui.QWidget` as ``baseinstance``.

    :method:`~PySide.QtCore.QMetaObject.connectSlotsByName()` is called on the
    created user interface, so you can implemented your slots according to its
    conventions in your widget class.

    Return ``baseinstance``, if ``baseinstance`` is not ``None``.  Otherwise
    return the newly created instance of the user interface.
    """
    loader = UiLoader(baseinstance)
    print(uifile)
    widget = loader.load(uifile)
    QtCore.QMetaObject.connectSlotsByName(widget)
    return widget


class MyMainWindow(QtGui.QMainWindow):
    def __init__(self, *args, **kwds):
        QtGui.QMainWindow.__init__(self, *args, **kwds)
        self.Base_Dir = os.path.dirname(os.path.realpath(__file__))
        wid = loadUi(os.path.join(self.Base_Dir, "Main.ui"), self)
        self.local_table_model = MediaLibrary.MediaLibrary(self, [])
        self.remote_table_model = MediaLibrary.MediaLibrary(self, [])
        self.left_playlist_table = PlaylistTable.PlaylistTable(self, [])
        self.right_playlist_table = PlaylistTable.PlaylistTable(self, [])
        self.LocalTableL.setModel(self.local_table_model)
        self.LocalTableR.setModel(self.local_table_model)
        self.RemoteTableL.setModel(self.remote_table_model)
        self.RemoteTableR.setModel(self.remote_table_model)
        self.LeftPlaylistTable.setModel(self.left_playlist_table)
        self.RightPlaylistTable.setModel(self.right_playlist_table)
        self.LocalTableL.setSortingEnabled(True)
        self.LocalTableR.setSortingEnabled(True)
        self.RemoteTableL.setSortingEnabled(True)
        self.RemoteTableR.setSortingEnabled(True)
        self.RightPlaylistTable.setSortingEnabled(True)
        self.LeftPlaylistTable.setSortingEnabled(True)
        self.AlbumList = {}
        self.sendQueue = queue.Queue()
        self.Id = 1
        self.local_server = None
        self.local_server_thread = None
        self.remote_server = None
        self.remote_server_thread = None
        self.menu = QtGui.QMenu(self)
        copy_action = QtGui.QAction('Copy File', self)
        copy_action.triggered.connect(self.copy_file)
        self.menu.addAction(copy_action)
        self.context_table = None
        self.present_dest = None
        PickleHandler.PickleReader(self.Base_Dir, self.local_table_model, self.remote_table_model)

    @QtCore.Slot()
    def local_edit_dirs(self):
        self.edit_dirs(local=True)

    @QtCore.Slot()
    def remote_edit_dirs(self):
        self.edit_dirs(local=False)

    @QtCore.Slot()
    def left_save_remote(self):
        self.save_playlist(self.left_playlist_table, local=False)

    @QtCore.Slot()
    def left_save_local(self):
        self.save_playlist(self.left_playlist_table, local=True)

    @QtCore.Slot()
    def right_save_remote(self):
        self.save_playlist(self.right_playlist_table, local=False)

    @QtCore.Slot()
    def right_save_local(self):
        self.save_playlist(self.right_playlist_table, local=True)

    def save_playlist(self, playlist_table, local=True):
        if not local:
            start_dir = Xbmc_Playlist
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

    @QtCore.Slot(QtCore.QPoint)
    def left_local_context(self, QPoint):
        self.context_table = self.LocalTableL
        self.present_dest = "Xbmc"
        self.menu.popup(QtGui.QCursor.pos())

    @QtCore.Slot(QtCore.QPoint)
    def right_local_context(self, QPoint):
        self.context_table = self.LocalTableR
        self.present_dest = "Xbmc"
        self.menu.popup(QtGui.QCursor.pos())

    @QtCore.Slot(QtCore.QPoint)
    def left_remote_context(self, QPoint):
        self.context_table = self.RemoteTableL
        self.present_dest = "Local"
        self.menu.popup(QtGui.QCursor.pos())

    @QtCore.Slot(QtCore.QPoint)
    def right_remote_context(self, QPoint):
        self.context_table = self.RemoteTableR
        self.present_dest = "Local"
        self.menu.popup(QtGui.QCursor.pos())

    def copy_file(self):
        print("Called Copy Action!")
        rows = self.context_table.selectionModel().selectedRows()
        if self.present_dest == "Xbmc":
            table_list = self.local_table_model.my_list
            target_dir = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory", Xbmc_Music))
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

    def edit_dirs(self, local=True):
        if local:
            dirs = str(QtGui.QFileDialog.getExistingDirectory(self, "Select Directory"))
        else:
            dirs = Xbmc_Music
        #print("Dirs = %s" % dirs)
        if local:
            table = self.local_table_model
        else:
            table = self.remote_table_model
        if table.add_root_dirs(dirs):
            MyMainWindow.scan_dir_to_table(table, dirs)
            print("Started")
        return

    @staticmethod
    def scan_dir_to_table(table, my_dir, ignore_files=()):
        print("Starting scan of %s" % (my_dir))
        table.server = FileScanner.LocalFileScanner(table.file_queue, table.dir_queue, ignore_files=ignore_files)
        table.server_thread = QtCore.QThread()
        table.server.set_params(my_dir, subdirs=True)
        table.server.moveToThread(table.server_thread)
        table.server.signal.connect(table.rows_from_server)
        table.server_thread.started.connect(table.server.run)
        table.server_thread.start()

    @QtCore.Slot()
    def sync_files(self):
        self.local_table_model.sync_prep()
        self.remote_table_model.sync_prep()
        self.local_table_model.sync_to(self.remote_table_model)
        self.remote_table_model.sync_to(self.local_table_model)

    @QtCore.Slot()
    def remote_quick_refresh(self):
        MyMainWindow.refresh(self.remote_table_model, ignore_files=self.remote_table_model.get_all_files())

    @QtCore.Slot()
    def local_quick_refresh(self):
        MyMainWindow.refresh(self.local_table_model, ignore_files=self.local_table_model.get_all_files())

    @QtCore.Slot()
    def local_full_refresh(self):
        MyMainWindow.refresh(self.local_table_model)

    @QtCore.Slot()
    def remote_full_refresh(self):
        MyMainWindow.refresh(self.remote_table_model)

    @staticmethod
    def refresh(table, ignore_files=()):
        if len(ignore_files) == 0:
            table.clear_all_rows()
        for my_dir in table.get_root_dirs():
            MyMainWindow.scan_dir_to_table(table, my_dir, ignore_files=ignore_files)

    @QtCore.Slot()
    def left_load_playlist(self):
        self.load_playlist(self.left_playlist_table)

    @QtCore.Slot()
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
    app = QtGui.QApplication(sys.argv)
    MainWindow = MyMainWindow()
    MainWindow.show()
    sys.exit(app.exec_())
