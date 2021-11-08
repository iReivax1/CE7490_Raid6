import os
import numpy as np
import logging
import shutil

from numpy.core.shape_base import block


class DiskObject(object):
    
    def __init__(self, dir, id, size, type='data'):
        self.id = id
        self.size = size
        self.type = type
        if self.type == 'P' or self.type == 'Q':
            self.override = False
        else:
            self.override = True
        self.dir = self.create_folders(disk_dir=os.path.join(dir, 'disk_%d' % id))
        self.data_file_path = None
        self.data_blocks = None
    
    
    def get_id(self):
        return self.id

    def read(self, id):
        with open(os.path.join(self.dir, 'disk_%d' % id), 'r') as f:
            return f.read()


    def write(self, id, data):
        with open(os.path.join(self.dir, 'disk_%d' % id), 'w') as f:
            for i in data:
                f.write(i)
            logging.info('Write done at{0}'.format(self.id))


    def get_data_block(self, stripe_size):
        data_content = self.read(id=self.id)

        size_content = len(data_content)
        data_blocks = []
        #if size of content is not multiple of stripe size
        # Padding remainder data with 0
        if size_content % stripe_size != 0:
            for _ in range(stripe_size - (size_content % stripe_size)):
                # data_content = str(data_content + 0
                print(data_content)
        
        assert size_content % stripe_size == 0
        #get blocks of data
        for i in range(0, size_content , stripe_size):
            end_of_block_idx = min(size_content, i+stripe_size)
            data_blocks.append(data_content[i:end_of_block_idx])
        self.data_blocks = data_blocks
        print(data_blocks)
        return data_blocks
    

    def create_folders(self, disk_dir):

        #if path dont exist
        if not os.path.exists(disk_dir):
            os.makedirs(disk_dir)
            logging.info('Disk {0} is created at {1}'.format(self.id, str(disk_dir)))
        else: #if exists alr delete 
            if self.override == True:
                shutil.rmtree(disk_dir)          
                os.makedirs(disk_dir)
            else :
                logging.info('Disk {0} is already created'.format(str(disk_dir)))
      
    
        
        return disk_dir 