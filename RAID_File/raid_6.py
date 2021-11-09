import galois 
import numpy as np
import concurrent.futures
from fileObject import FileObject
import logging
from copy import deepcopy
from galois_wrappers_v2 import create_parities
import galois_functions as gf


GF256 = galois.GF(2**8)

class RAID(object):

    def __init__(self, disk_list,num_normal_disk,parity_disk, q_disk, stripe_size):
        super().__init__()
        '''
        disk_list is all the normal data list, indexed from 0 to num_of_normal_disk
        '''
        self.disk_list = disk_list
        self.num_normal_disk = num_normal_disk
        self.parity_disk = parity_disk 
        self.q_disk = q_disk
        self.stripe_size = stripe_size
        # if gf is None:
        #     self.gf = GF256(num_data_disk=self.num_normal_disk,
        #                           num_checksum=self.num_parity_disk)
        # else:
        #     self.gf = GF256
        self.gf = GF256
        
        self.data_blocks = None
        #gf stuff   
        self.parity_int = None
        self.parity_char = None
        self.block_to_disk_mapping = None

    #striping technique when writing file. 
    def stripe_data_build_parity(self, data_block_list):
        self.data_blocks = data_block_list
        data = self.striping_data_blocks_to_raid_disks(num_data_disks= self.num_normal_disk ,
                                                 data_blocks=data_block_list)
        #disk list is a list ob diskobject

        # P, Q, drive_list = create_parities(self.disk_list)
        # print(P)
        # print(Q)
        # self.parity_disk.write(id =-1 , data=P)
        # self.q_disk.write(id =-2 , data=Q)
                                                           
        disk_iterator = zip(self.disk_list, data)
        print (disk_iterator)
        for disk, data in disk_iterator:
            print(disk)
            disk.write(id = disk.get_id() , data=''.join(self.check_empty_char(datum) for datum in data))
        
        # return P , Q
   
    #corrupted disks 
    def read_all_non_parity_disk(self, corrupted_disk_index=()):
    
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_normal_disk) as executor:
            res = list(executor.map(FileObject.read(id=i), self.disk_list))

        removed_res = []
        for i, re in enumerate(res):
            if i not in corrupted_disk_index:
                removed_res.append(re)

        return removed_res
    
    
    
    ###### Utilities
    def get_disk_ids(self):
        disk_ids = []
        for i in self.disk_list:
            disk_ids.append(i.get_id())
        return disk_ids
    
    def get_disk_list(self):
        return self.disk_list
    
    
    ##### For the creation of parity drives
    def compute_Q(self, write = False):
        Q = GF256(0)
        for i in self.get_disk_list():
            q = gf.q_drive_encoder(gf.convert_to_int(i.get_data_block(self.stripe_size)), i.get_id())
            Q = Q + q
        Q = gf.convert_to_numpy(Q)
        if write:
            Q = gf.convert_to_chr(Q)
            self.q_disk.write(Q)
            return "Q has been computed and written to the Q drive"
        else:
            return Q
            
    def compute_P(self, write = False):
        P = GF256(0)
        for i in self.get_disk_list():
            p = gf.drive_to_gf(gf.convert_to_int(i.get_data_block(self.stripe_size)))
            P = P + p
        P = gf.convert_to_numpy(P)
        if write:
            P = gf.convert_to_chr(P)
            self.parity_disk.write(P)
            return "P has been computed and written to the P drive"        
        else:
            return P
    
    
    ##### Retrieve parity information
    def get_Q(self):
        return gf.convert_to_int(self.q_disk.get_data_block(self.stripe_size))
    
    def get_P(self):
        return gf.convert_to_int(self.parity_disk.get_data_block(self.stripe_size))
    
    
    ##### Check for drive failure
    def check_for_failure(self):
        P_test = self.compute_P()
        Q_test = self.compute_Q()
        P = self.get_P()
        Q = self.get_Q()
        
        P_check = P_test == P
        Q_check = Q_test == Q
        
        print(P_check)
        print(Q_check)
        
        if P_check.all() and Q_check.all():
            return "No failures"
        else:
            return "At least one failure"
        
    
    
    
    def compute_parity(self, data):
        """
        Compute the parity giving the data
        :param data: file data in bytes format
        :return: return the parity in the char format
        """
        str_data = [list(map(self._byte_to_str, data_i.tolist())) for data_i in data]
        int_data = list(map(self._str_to_order, str_data))
        self.parity_int, self.parity_char = self.gf(data=np.array(int_data))
        logging.info('result of compute parity:\n{0}'.format(self.parity_int))
        return self.parity_char

    def check_corruption(self, disk_data_in_int):
        """
        Detect if single disk occurred silent corruption.
        :return: A boolean, True for failed, False for not.
        """
        new_parity, _ = self.gf.gen_parity(disk_data_in_int[0:self.config.data_disk_count])
        logging.info('Check silent corruption\nNew parity is {0}'.format(new_parity))
        logging.info('Old parity is {0}'.format(self.parity_int))
        res = np.bitwise_xor(np.array(self.parity_int), np.array(new_parity))
        if np.count_nonzero(res) == 0:
            logging.log_str('No corruption')
        else:
            logging.log_str('Exist corruption!!!')
        pass


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

    def _gaussian_elimination(self, augmented_matrix):
        """
        Function to recover the disks using the gaussian elimination method
        :param augmented_matrix: augmented matrix in gaussian elimination process
        :return:
        """
        rows = np.array(augmented_matrix).shape[0]
        eliminated_flag = [False for _ in range(rows)]
        for i in range(rows):
            if np.sum(eliminated_flag) == rows:
                break
            find_index = 0
            while eliminated_flag[find_index] is True or augmented_matrix[i][find_index] == 0:
                find_index += 1
            eliminated_flag[find_index] = True
            for j in range(rows):
                if j != i and augmented_matrix[j][find_index] != 0:
                    value_i = augmented_matrix[i][find_index]
                    value_j = augmented_matrix[j][find_index]
                    for k in range(len(augmented_matrix[i])):
                        tmp_i_val = self.gf.multiply(augmented_matrix[i][k], value_j)
                        augmented_matrix[j][k] = self.gf.multiply(augmented_matrix[j][k], value_i)
                        augmented_matrix[j][k] = self.gf.sub([augmented_matrix[j][k],
                                                              tmp_i_val])
                    assert augmented_matrix[j][find_index] == 0
        res = [0 for _ in range(rows)]
        for i in range(rows):
            assert np.count_nonzero(augmented_matrix[i][0:rows]) >= 1
            res[np.nonzero(augmented_matrix[i])[0][0]] = self.gf.divide(augmented_matrix[i][-1],
                                                                        augmented_matrix[i][
                                                                            np.nonzero(augmented_matrix[i])[0][0]])
        return res

    #striping from temp data disk to the raid disks
    def striping_data_blocks_to_raid_disks(self, num_data_disks, data_blocks):
        disk_index = 0
        data_blocks_per_disk = 0
        data_disk = []
        self.block_to_disk_mapping = []        
        for _ in range(num_data_disks):
            data_disk.append([])
        #data blocks is the data in stripe size already
        for data_block in data_blocks:
            
            data_disk[disk_index].append(data_block)

            self.block_to_disk_mapping.append((disk_index, len(data_disk[disk_index]) - 1))
            #only write to disk in multiple of num_data_disks
            disk_index = (disk_index + 1) % num_data_disks

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
        print( np.array(data_disk))   
        return np.array(data_disk)

    
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



