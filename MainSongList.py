from PyQt5.QtCore import QObject, pyqtSignal


class MainSongList(QObject):
    base_keys = ("title", "album", "artist", "genre", "year", "track", "length", "image",
                     "size", "file")             # Keys of an item in the base list
    sync_criteria = ("title", "artist", "length")
    valid_criteria = ("title", "album", "artist", "genre", "year", "track", "length", "image",
                     "size")
    main_list_keys = ("title", "album", "artist", "genre", "year", "track", "length", "image",
                     "size", "remote version", "local version", "base_index", "local count", "remote count")
    copy_keys = ("title", "album", "artist", "genre", "year", "track", "length", "image",
                     "size")
    initial_lists = ("remote version", "local version", "base_index")

    def __init__(self, *args, **kwargs):
        mylist = kwargs.pop("mylist")
        super().__init__()
        self.song_list = []
        self.base_list = {}
        self.add_songs(mylist)
        # load previous list from pickle?

    def rebuild_display(self):
        for song in self.base_list:
            self.add_song(song)

    def clear_display(self):
        self.song_list = []

    def clear_all(self):
        self.base_list = {}
        self.clear_display()

    def prep_songs(self, songs):
        fn_list = [x['file'] for x in songs]
        fn_list.reverse()
        for i, fn in enumerate(fn_list):
            if fn in self.base_list:
                del(songs[len(songs)-i-1])
        new_rows = len(songs)
        for i, song in enumerate(songs):
            song_index = self.find_matching_song(song)
            if song_index > -1:
                new_rows -= 1
                song["dupe"] = song_index
            elif (self.find_matching_song(song, search_list=songs[i+1:]) == -1):
                song["dupe"] = song_index
        return new_rows, songs

    def add_songs(self, songs):
        for song in songs:
            self.add_song(song)

    def add_song(self, song):
        if "dupe" not in song:
            _, songlist = self.prep_songs([song])
            if len(songlist) < 1:
                return
            song = songlist[0]
        song_index = song["dupe"]
        del(song["dupe"])
        if song_index > -1:
            return self.add_duplicate_song(song, index=song_index)
        self._add_to_base(song)
        newsong = {x:song.get(x, None) for x in self.copy_keys}
        for k in self.initial_lists:
            newsong[k] = []
        filename = song.get('file', "")
        if self.song_is_remote(filename):
            newsong["remote version"].append(filename)
            newsong["local count"] = 0
            newsong["remote count"] = 1
        else:
            newsong["local version"].append(filename)
            newsong["local count"] = 1
            newsong["remote count"] = 0
        self.song_list.append(newsong)

    def find_matching_song(self, song, criteria=None, search_list = None):
        if criteria is None:
            criteria = self.sync_criteria
        criteria_set = frozenset([(i, song[i]) for i in criteria])
        if search_list:
            return next((index for index, value in enumerate(search_list) if criteria_set.issubset([(k, value.get(k, "")) for k in criteria])),
                        -1)
        return next((index for index, value in enumerate(self.song_list) if
                     criteria_set.issubset([(k, value.get(k, "")) for k in criteria])),
                    -1)

    def add_duplicate_song(self, song, index):
        filename = song.get('file', "")
        is_remote = self.song_is_remote(filename)
        if filename in self.song_list[index]["remote version"] or filename in self.song_list[index]["local version"]:
            return
        self._add_to_base(song)
        if is_remote:
            self.song_list[index]["remote count"] += 1
            self.song_list[index]["remote version"].append(filename)
        else:
            self.song_list[index]["local count"] += 1
            self.song_list[index]["local version"].append(filename)
        for x in self.song_list[index]:
            if self.song_list[index][x] == None:
                self.song_list[index][x] = song.get(x, None)

    def _add_to_base(self, song):
        checked_song = {x:song.get(x, "") for x in self.base_keys}
        self.base_list[song["file"]] = checked_song

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

    def get_all_files(self):
        return self.base_list.keys()