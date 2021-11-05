import os
import numpy as np
import logging

from numpy.core.shape_base import block


class DiskObject(object):
    
    def __init__(self, dir, id, size, type='data', override=False):
        self.id = id
        self.size = size
        self.type = type
        self.dir = self.create_folders(disk_dir=os.path.join(dir, '_disk_%d' % id))
        self.data_file_path = None
        self.data_blocks = None
        self.override_enabled = override
    
    def get_id(self):
        return self.id

    def read(self, id):
        with open(os.path.join(self.dir, '_disk_%d' % id), 'rb') as f:
            return f.read()

    def write(self, id, data):
        with open(os.path.join(self.dir, '_disk_%d' % id), 'wb') as f:
            f.write(data)
            logging.info('Write done at{0}'.format(self.id))


    def get_data_block(self, stripe_size):
        data_content = self.read(id=self.id)
        size_content = len(data_content)
        data_blocks = []
        #if size of content is not multiple of stripe size
        # Padding remainder data with 0
        if size_content % stripe_size != 0:
            data_content += [0 for _ in range(stripe_size - (size_content % stripe_size))]
        
        assert size_content % stripe_size == 0
        
        for i in range(0, size_content , stripe_size):
            end_of_block_idx = min(size_content, i+stripe_size)
            data_blocks.append(data_content[i:end_of_block_idx])
        self.data_blocks = data_blocks
        return data_blocks
    

    def create_folders(self, disk_dir):
        if os.path.isdir(disk_dir) and self.override_enabled is False:
            raise ValueError('Disk {} already existed'.format(disk_dir))
        else:
            os.mkdir(disk_dir)
            logging.info('Disk {0} is created at {1}'.format(self.id, str(disk_dir)))
        
        return disk_dir