__author__ = 'pscheidler'
import mutagenx
import os


class MediaTranslate:
    tags = {"mp3": {"album": "TALB", "title": "TIT2", "genre": "TCON", "year": "TDRC", "artist": "TPE1"},
            "m4a": {"album": b'\xa9alb', "title": b'\xa9nam', "genre": b'\xa9gen', "year": b'\xa9day',
                    "artist": b'\xa9ART'}}

    @staticmethod
    def get_info(file_name):
        file_type = file_name[-3:]
        if file_type not in MediaTranslate.tags:
            return None
        file_obj = mutagenx.File(file_name)
        return_val = {"file": file_name,
                      "size": os.path.getsize(file_name),
                      "length": int(file_obj.info.length)
                      }
        for i in MediaTranslate.tags[file_type]:
            if MediaTranslate.tags[file_type][i] in file_obj:
                return_val[i] = MediaTranslate.list_strip(file_obj[MediaTranslate.tags[file_type][i]])
            else:
                return_val[i] = ""
        return return_val

    @staticmethod
    def list_strip(in_val):
        if type(in_val) is str:
            return in_val
        return in_val[0]

    @staticmethod
    def get_dir_info(my_dir, my_files=None, sync_state=None):
        if not os.path.exists(my_dir):
            print("No such directory")
            return []
        if my_files is None:
            my_files = os.listdir(my_dir)
        return_value = []
        for fn in my_files:
            file_info = MediaTranslate.get_info(os.path.join(my_dir, fn))
            if file_info:
                if sync_state:
                    file_info["sync state"] = sync_state
                return_value.append(file_info)
       # print(return_value)
        return return_value

    @staticmethod
    def playlist_name(file_name):
        return_name = file_name
        if return_name.startswith('C:'):
            return return_name[2:]
        return_name = return_name.replace('\\\\192.168.1.138\\Music', '/storage/music')
        return_name = return_name.replace('\\', '/')
        return return_name

    @staticmethod
    def local_name(file_name):
        return_name = file_name
        if '\\' in return_name and not return_name.startswith('C'):
            return_name = 'C:' + return_name
        return_name = return_name.replace('/storage/music', '\\\\192.168.1.138\\Music')
        return_name = return_name.replace('/', '\\')
        return return_name

    @staticmethod
    def get_partner_file(song_info):
        if isinstance(song_info["partner"], str) and len(song_info["partner"]) > 2:
            file_name = song_info["partner"]
            result = ["good", file_name]
        elif isinstance(song_info["partner"], list):
            #print("Using close match... for %s" % (song_info["file"]))
            file_name = song_info["partner"][0]
            result = ["close", file_name]
        else:
            #print("No match for %s" % (song_info["file"]))
            file_name = None
            result = ["none", song_info["file"]]
        return result, file_name

    @staticmethod
    def song_to_playlist(song_info, local=True):
        length = song_info["length"]
        if not length:
            length = 1
        file_name = song_info["file"]
        result = ["good", file_name]
        if file_name.startswith('C:'):
            if not local:
                result, file_name = MediaTranslate.get_partner_file(song_info)
        else:
            if local:
                result, file_name = MediaTranslate.get_partner_file(song_info)
        if not file_name:
            return result, ""
        file_name = MediaTranslate.playlist_name(file_name)
        return result, '#EXTINF:%i,%s - %s\n%s\n' % (length, song_info['artist'], song_info['title'], file_name)
