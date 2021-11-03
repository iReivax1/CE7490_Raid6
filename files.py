import os
import sys
import glob
import numpy as np
import string

from copy import deepcopy


class File(object):
    """
    A class that represent a real file that need to be stored in the RAID 6 system.
    """

    def __init__(self):
        self._file_content = None

    @property
    def file_content(self):
        return np.array(self._file_content).tostring()

    @file_content.setter
    def file_content(self, val):
        self._file_content = val

    def random_generate_string(self, data_size):
        self.file_content = np.random.choice(list(string.ascii_letters), size=data_size)
        Logger.log_str(log_str='Random generate a string: {}'.format(str(self.file_content.decode('utf-8'))))

    @staticmethod
    def byte_to_string(bytes_data):
        assert isinstance(bytes_data, bytes)
        return str(bytes_data.decode('utf-8'))

    def update(self, index, new_char):
        """
        Update the file at a certain index with new char. This method is only used for class attributes maintain,
        and is not part of the RAID 6 process
        :param index:
        :param new_char:
        :return:
        """
        assert index < len(self._file_content)
        old_file = deepcopy(self._file_content)
        self._file_content[index] = new_char
        Logger.log_str('File is updated from: \n{} \nto \n{}'.
                       format("".join(val for val in old_file), "".join(val for val in self._file_content)))
