import galois 
import numpy as np
import concurrent.futures
from fileObject import FileObject
import logging
from copy import deepcopy
import galois_functions as gf
from diskObject import DiskObject

GF256 = galois.GF(2**8)

class RAID(object):

    def __init__(self, root_dir, num_normal_disk, size_of_disk, stripe_size):
        super().__init__()
        '''
        disk_list is all the normal data list, indexed from 0 to num_of_normal_disk
        '''
        #Disk Object Parameters
        self.root_dir = root_dir
        self.num_normal_disk = num_normal_disk
        self.size_of_disk = size_of_disk
        self.stripe_size = stripe_size
        
        #Disk Variables
        self.disk_list = []
        self.p_disk = self.create_disk(-1,'P')
        self.q_disk = self.create_disk(-2,'Q')        
        
    
        self.block_to_disk_mapping = None
        
        
        for idx in range(self.num_normal_disk):
            self.disk_list.append(self.create_disk(disk_id = idx, disk_type = 'data'))
    
    
    ###### Utilities
    def create_disk(self, disk_id, disk_type):
        return DiskObject(disk_dir=self.root_dir, disk_id=disk_id, size=self.size_of_disk, stripe_size = self.stripe_size, type=disk_type)
    
    def add_new_data_disk(self, data, disk_id):
        '''
        data must be in chr() format
        disk_id must be integer
        '''
        self.disk_list.append(self.create_disk(disk_id,'data'))
        self.disk_list[-1].write(data)
        return "New disk added and data written to disk"
    
    def get_disk_ids(self):
        disk_ids = []
        for i in self.disk_list:
            disk_ids.append(i.get_id())
        return disk_ids
    
    def get_disk_list(self):
        return self.disk_list
    
    
    ##### For the creation of parity drives
    def compute_Q(self, write = False):
        '''
        if write is True, will write to the corresponding disk as chr()
        Otherwise will return int() as a numpy array
        '''
        
        Q = GF256(0)
        for i in self.get_disk_list():
            q = gf.q_drive_encoder(gf.convert_to_int(i.get_data_block()), i.get_id())
            Q = Q + q
        Q = gf.convert_to_numpy(Q)
        if write:
            Q = gf.convert_to_chr(Q)
            self.q_disk.write(Q)
            return "Q has been computed and written to the Q drive"
        else:
            return Q
            
    def compute_P(self, write = False):
        '''
        if write is True, will write to the corresponding disk as chr()
        Otherwise will return int() as a numpy array
        '''
        
        P = GF256(0)
        for i in self.get_disk_list():
            p = gf.drive_to_gf(gf.convert_to_int(i.get_data_block()))
            P = P + p
        P = gf.convert_to_numpy(P)
        if write:
            P = gf.convert_to_chr(P)
            self.p_disk.write(P)
            return "P has been computed and written to the P drive"        
        else:
            return P
    
    
    ##### Retrieve parity information
    def get_Q(self):
        '''
        returns an int() numpy array
        '''
        return gf.convert_to_int(self.q_disk.get_data_block())
    
    def get_P(self):
        '''
        returns an int() numpy array
        '''
        return gf.convert_to_int(self.p_disk.get_data_block())
    
    
    ##### Check for drive failure
    def check_for_failure(self):
        
        if self.p_disk == None:
            return "P disk failure"
        if self.q_disk == None:
            return 'Q disk failure'
        
        P_test = self.compute_P()
        Q_test = self.compute_Q()
        P = self.get_P()
        Q = self.get_Q()
        
        P_check = P_test == P
        Q_check = Q_test == Q
        
        # print(P_check)
        # print(Q_check)
        
        if P_check and Q_check:
            return "No failures"
        else:
            return "At least one failure"

            
<<<<<<< HEAD
   
=======
    def update_data(self, block_global_index, new_data_block):
        """
        Update the file
        :param block_global_index: the block's index that need to be updated
        :param new_data_block: new data block
        :return: None
        """
        # First get the block position in the RAID 6

        disk_id, chuck_id = self.block_to_disk_mapping[block_global_index]
        self.data_block_list[block_global_index] = new_data_block
        str_data = self._byte_to_str(new_data_block)
        int_data = self._str_to_order(str_data)[0]

        # Generate the new parity, by only computing the block that is changed.

        parity_int, parity_char = self.gf.gen_parity(data=np.array(int_data).reshape([1, -1]))
        logging.info(log_str='Get the parity:\n{}'.format(self.parity_int))
        parity_char = parity_char.reshape([-1])
        parity_int = parity_int.reshape([-1])

        # Update the parity (only for class attribute maintenance)
        for i in range(self.config.parity_disk_count):
            self.parity_int[i][chuck_id] = parity_int[i]
            self.parity_char[i][chuck_id] = parity_char[i]
        logging.info(log_str='Get the updated parity:\n{}'.format(self.parity_int))

        # Write the updated data and parity to disks
        for i in range(self.config.data_disk_count, self.config.disk_count):
            disk = self.disk_list[i]
            disk.write_to_disk(disk=disk, data="".join(
                self.no_empty_chr(val) for val in self.parity_char[i - self.config.data_disk_count]), mode='w')
        disk = self.disk_list[disk_id]

        old_data_block = disk.read(disk=disk)
        res = self._byte_to_str(old_data_block)
        new_res = list(deepcopy(res))
        new_res[chuck_id] = self._byte_to_str(new_data_block)[0]
        new_res = "".join(new_res)
        disk.write(disk=disk, data="".join(self.no_empty_chr(val) for val in new_res),
                            mode='w')

    # #striping from temp data disk to the raid disks
    def striping_data_blocks_to_raid_disks(self, data_blocks):
        disk_index = 0
        data_blocks_per_disk = 0
        data_disk = []
        self.block_to_disk_mapping = []        
        for _ in range(self.num_normal_disk):
            data_disk.append([])
        
        #data blocks is the data in stripe size already
        for data_block in data_blocks:
            
            data_disk[disk_index].append(data_block)

            self.block_to_disk_mapping.append((disk_index, len(data_disk[disk_index]) - 1))
            #only write to disk in multiple of num_data_disks
            disk_index = (disk_index + 1) % self.num_normal_disk

        pad_block = self.pad_char(length=len(data_blocks[0]))
        
        assert len(pad_block) == len(data_blocks[0])
        
        for data in data_disk:
            data_blocks_per_disk = max(data_blocks_per_disk, len(data))
        
        #padding to ensure the data block size in the disk is == stripe size
        for index, data in enumerate(data_disk):
            if len(data) < data_blocks_per_disk:
                for _ in range(data_blocks_per_disk - len(data)):
                    data_disk[index].append(pad_block)
        for data in data_disk:
            assert len(data) == data_blocks_per_disk
        
        # print( np.array(data_disk))
        count = 0
        for i in self.get_disk_list():
            i.write(data_disk[count])
            count += 1
            
           
        return 'data disks written'

    
    def check_empty_char(self, datum):
    
        assert isinstance(datum, str)
        if datum == '' or datum == None:
            #chr 32 returns space
            return chr(32)
        else:
            return datum
  
    def pad_char(self, length):
        assert length % 4 == 0
        return np.array(['' for _ in range(length - (length%4))])


    def str_to_int(self, string_data):
        assert isinstance(string_data[0], str)
        res = []
        for i in range(len(string_data)):
            if len(string_data[i]) > 0:
                res.append(ord(string_data[i]))
            else:
                res.append(0)
        return np.array(res, dtype=np.uint8)
>>>>>>> 794fc4f5600f4cd18fd17a5f9f76496659d62f14
