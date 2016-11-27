__author__ = 'pscheidler'

import os.path
import pickle


class PickleReader:
    PickleFileName = "data.p"

    def __init__(self, my_dir, local_table, remote_table):
        self.my_file_name = os.path.join(my_dir, self.PickleFileName)
        self.PickleFile = None
        if os.path.isfile(self.my_file_name):
            self.PickleFile = open(self.my_file_name, 'rb')
        else:
            return
        self.Version = self.get_item()
        self.get_table_info(local_table)
        self.get_table_info(remote_table)
        self.PickleFile.close()

    def get_item(self):
        if self.PickleFile:
            return pickle.load(self.PickleFile)
        return None

    def get_table_info(self, table):
        item = self.get_item()
        if item :
            table.set_contents(self.get_item())


class PickleWriter:
    PickleFileName = "data.p"
    Version = 1

    def __init__(self, my_dir, local_table, remote_table):
        self.my_file_name = os.path.join(my_dir, self.PickleFileName)
        self.PickleFile = open(self.my_file_name, 'wb')
        pickle.dump(self.Version, self.PickleFile)
        self.set_table_info(local_table)
        self.set_table_info(remote_table)
        self.PickleFile.close()

    def get_item(self):
        if self.PickleFile:
            return pickle.load(self.PickleFile)
        return None

    def set_table_info(self, table):
        pickle.dump(table.get_contents(), self.PickleFile)
