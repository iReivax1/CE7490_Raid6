import os
import numpy as np
import logging


class DiskObject(object):
    
    def __init__(self, disk_path, id, disk_size, disk_type='data', override_path=False):
        self.id = id
        self.disk_size = disk_size
        self.disk_type = disk_type
        self.disk_path = self.create_disk_folder(disk_path=os.path.join(disk_path, 'disk_%d' % id),
                                                 override_path=override_path)
        self.data_file_path = None
        self.block_list = None

    def create_disk_folder(self, disk_path, override_path=False):
        if os.path.isdir(disk_path) and override_path is False:
            raise ValueError('Disk %s already existed' % disk_path)
        os.mkdir(disk_path)
        logging.info(log_str=str('Disk %d is created at %s' % (self.id, disk_path)))
        return disk_path

    @staticmethod
    def write_to_disk(disk, data, mode='wb'):
        with open(os.path.join(disk.disk_path, 'data'), mode) as f:
            f.write(data)
            disk.data_file_path = os.path.join(disk.disk_path, 'data')
            logging.info(log_str='Data is written into %s' % disk.data_file_path)

    @staticmethod
    def read_from_disk(disk, mode='rb'):
        with open(disk.data_file_path, mode) as f:
            return f.read()

    def set_up_data_block_list(self, block_size):
        assert self.data_file_path is not None
        content = self.read_from_disk(disk=self)
        if len(content) % block_size != 0:
            content += [0 for _ in range(block_size - len(content) % block_size)]
        assert len(content) % block_size == 0

        block_list = [content[i: min(len(content), i + block_size)] for i in range(0, len(content), block_size)]
        self.block_list = block_list
        return block_list
