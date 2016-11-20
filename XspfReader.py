__author__ = 'pscheidler'
import xml.etree.ElementTree as etree
import urllib.parse

class XspfReader:

    def __init__(self, file_name):
        self.root = etree.parse(file_name).getroot()

    def get_track_list(self):
        for child in self.root:
            if 'trackList' in child.tag:
                return child

    def get_file_list(self):
        return_list = []
        for track in self.get_track_list():
            if 'track' not in track.tag:
                continue
            for item in track:
                if 'location' in item.tag:
                    return_list.append(XspfReader.clean_file_name(item.text))
                    break
        return return_list

    @staticmethod
    def clean_file_name(name):
        if 'file:///' in name:
            name = name[len('file:///'):]
        name = urllib.parse.unquote(name)
        print(name)
        name = name.replace('/', '\\').strip().lower()
        return name
