__author__ = 'pscheidler'
from MediaLibrary import MediaLibrary
from MediaTranslate import MediaTranslate


class PlaylistTable(MediaLibrary):
    def __init__(self, parent, mylist, *args):
        super().__init__(parent, mylist, *args)

    def save(self, file_name, local=True):
        log_msg = {"close":[], "none":[]}
        write_str = "#EXTM3U\n"
        with open(file_name, 'w') as fp:
            fp.write(write_str)
        write_str = ""
        for x in self.my_list:
            result, new_str = MediaTranslate.song_to_playlist(x, local=local)
            write_str += new_str
            if result[0] == "close":
                log_msg["close"].append([x["file"], result[1]])
            elif result[0] == "none":
                log_msg["none"].append(result[1])
            if len(write_str) > 10000:
                with open(file_name, 'a') as fp:
                    fp.write(write_str)
                    write_str = ""
        with open(file_name, 'a') as fp:
            fp.write(write_str)
        return log_msg