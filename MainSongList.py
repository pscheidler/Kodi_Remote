from PyQt5.QtCore import QObject, pyqtSignal


class MainSongList(QObject):
    base_keys = ("title", "album", "artist", "genre", "year", "track", "length", "image",
                     "size", "file")             # Keys of an item in the base list
    sync_criteria = ("title", "artist", "length")
    main_list_keys = ("title", "album", "artist", "genre", "year", "track", "length", "image",
                     "size", "remote version", "local version", "base_index")
    copy_keys = ("title", "album", "artist", "genre", "year", "track", "length", "image",
                     "size")
    initial_lists = ("remote version", "local version", "base_index")

    def __init__(self, *args, **kwargs):
        self.song_list = []
        self.base_list = {}
        # load previous list from pickle?

    def find_matching_song(self, criteria):
        if isinstance(criteria, dict):
            criteria_set = set(criteria.items())
        else:
            criteria_set = criteria
        return next((index for index, value in enumerate(self.song_list) if criteria_set.issuperset(value.items())), default=-1)

    def add_duplicate_song(self, song, index):
        filename = song.get('file', "")
        is_remote = self.song_is_remote(filename)
        if filename in self.song_list[index]["remote version"] or filename in self.song_list[index]["local version"]:
            return
        self._add_to_base(song)
        if is_remote:
            self.song_list[index]["remote version"].append(filename)
        else:
            self.song_list[index]["local version"].append(filename)
        for x in self.song_list[index]:
            if self.song_list[index][x] == None:
                self.song_list[index][x] = song.get(x, None)

    def _add_to_base(self, song):
        checked_song = {x:song.get(x, "") for x in self.base_keys}
        self.base_list[song["file"]] = checked_song

    def add_song(self, song, pre_checked=False):
        if not pre_checked:
            criteria = set([song[i] for i in self.sync_criteria])
            song_index = self.find_matching_song(criteria)
            if song_index > -1:
                return self.add_duplicate_song(song, index=song_index)
        self._add_to_base(song)
        newsong = {x:song.get(x, None) for x in self.copy_keys}
        for k in self.initial_lists:
            newsong[k] = []
        filename = song.get('file', "")
        if self.song_is_remote(filename):
            newsong["remote version"].append(filename)
        else:
            newsong["local version"].append(filename)
        self.song_list.append(newsong)

    @staticmethod
    def song_is_remote(filename):
        if '192' in filename[0:6]:
            return True
        return False

    def set_new_match_criteria(self, criteria):
        self.sync_criteria = tuple(criteria)
        self.song_list = []
        for x in self.base_list:
            self.add_song(self.base_list[x])