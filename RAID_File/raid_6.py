import galois 
import numpy as np
import concurrent.futures
from fileObject import FileObject
import math
import logging
from copy import deepcopy


GF256 = galois.GF(2**8)

class RAID(object):

    def __init__(self, disk_list,num_normal_disk,num_parity_disk, gf=None):
        super().__init__()
        self.disk_list = disk_list
        self.num_normal_disk = num_normal_disk
        self.num_parity_disk = num_parity_disk 
        # if gf is None:
        #     self.gf = GF256(num_data_disk=self.num_normal_disk,
        #                           num_checksum=self.num_parity_disk)
        # else:
        #     self.gf = GF256
        self.gf = GF256
        
        self.data_blocks = None
        #gf stuff    
        self.gf_matrix = self.gf.gen_matrix_A()
        self.parity_int = None
        self.parity_char = None
        self.block_to_disk_mapping = None

    #striping technique when writing file
    def write_file(self, data_block_list):
        self.data_blocks = data_block_list
        data = self.striping_data_blocks_to_raid_disks(num_data_disks= self.num_normal_disk ,
                                                 data_blocks=data_block_list,
                                                 num_block_per_chunk=2)
        #add parity bits to column                                                 
        data_with_parity = (np.concatenate([data, self.compute_parity(data=data)], axis=0)).tolist()
        
        disk_iterator = zip(self.disk_list, data_with_parity)

        for disk, data in disk_iterator:
            disk.write(id = disk.get_id() , data=''.join(self.check_empty_char(datum) for datum in data), mode='w')


    def read_from_disk_and_generate_data(self):
        '''???'''
        res = self.read_all_non_parity_disk()
        res = [re.tolist() for re in res][0:self.num_normal_disk ]
        new_res = []
        for i, j in self.block_to_disk_mapping:
            new_res.append(res[i][j])
        logging.info(
            'Data is {}'.format(self._int_data_to_string(new_res, non_zero_flag=False)))


    def read_all_non_parity_disk(self, corrupted_disk_index=()):
    
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_normal_disk) as executor:
            res = list(executor.map(FileObject.get_file_content(), self.disk_list))

        removed_res = []
        for i, re in enumerate(res):
            if i not in corrupted_disk_index:
                removed_res.append(re)
        removed_res = self._byte_to_int_all_disk(removed_res, conf=self.config)

        return removed_res

    

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

    def recover_disk(self, corrupted_disk_index=()):
        """
        Recover the data by using gaussian elimination
        :param corrupted_disk_index: a list contain the corrupted disk indexes
        :return: None
        """
        logging.log_str('Corrupted disks detected: {0}, preparing to disk recovery'.format(corrupted_disk_index))

        # Retrieve the good disks data: vector_e_new and corresponding encode matrix rows: matrix_a_new
        matrix_a_new, vector_e_new = self.gf.recover_matrix(mat_a=self.gf_matrix,
                                                            vec_e=self.read_all_non_parity_disk(corrupted_disk_index),
                                                            corrupt_index=corrupted_disk_index)
        data_strip_count = vector_e_new.shape[1]
        new_data = []
        for i in range(data_strip_count):
            augmented_matrix = np.concatenate((matrix_a_new, np.reshape(vector_e_new[:, i], [-1, 1])), axis=1)
            # Gaussian elimination is carried out in a block by block manner
            new_data.append(self._gaussian_elimination(augmented_matrix))
        new_data = np.transpose(new_data)
        self.parity_int, self.parity_char = self.gf.gen_parity(new_data)
        logging.info(log_str='Recovered disks: {}'.format(corrupted_disk_index))
        new_data = self._int_data_to_chr(data=new_data)
        data_with_parity = np.concatenate([new_data, self.parity_char], axis=0)
        # Write the recovered data to disks
        for i, disk, data in zip(range(self.config.disk_count), self.disk_list, data_with_parity.tolist()):
            if i in corrupted_disk_index:
                disk.write_to_disk(disk=disk, data="".join(self.no_empty_chr(val) for val in data), mode='w')
        logging.log_str('Recovered data is written to disk')

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
    def striping_data_blocks_to_raid_disks(self, num_data_disks, data_blocks, num_block_per_chunk):
        disk_index = 0
        data_blocks_per_disk = 0
        data_disk = []
        self.block_to_disk_mapping = []        
        for _ in range(num_data_disks):
            data_disk.append([])
        #data blocks is the data in stripe size already
        for i, j in enumerate(data_blocks):
            if isinstance(j, str):
                data_disk.append([])
                data_disk[disk_index].append(self.str_to_int(j))
            else:
                data_disk[disk_index].append(j)

            self.block_to_disk_mapping.append((disk_index, len(data_disk[disk_index]) - 1))

            if (i + 1) % num_block_per_chunk == 0:
                disk_index = (disk_index + 1) % num_data_disks

        padding_block = self.pad_char(length=len(data_blocks[0]))
        
        assert len(padding_block) == len(data_blocks[0])
        
        
        for data in data_disk:
            data_blocks_per_disk = max(data_blocks_per_disk, len(data))
        
        #padding to ensure the data block size in the disk is == stripe size
        for index, data in enumerate(data_disk):
            if len(data) < data_blocks_per_disk:
                for _ in range(data_blocks_per_disk - len(data)):
                    data_disk[index].append(padding_block)
        for data in data_disk:
            assert len(data) == data_blocks_per_disk
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
        return np.array([' ' for _ in range(length // 4)])


    def str_to_int(self, string_data):
        assert isinstance(string_data[0], str)
        res = []
        for i in range(len(string_data)):
            if len(string_data[i] > 0 ):
                res.append(ord(string_data[i]))
            else:
                res.append(0)
        return np.array(res, dtype=np.uint8)
    # Below are some conversion for different data formats: bytes, string, char, int

    @staticmethod
    def _str_to_order_for_parity(stri, zero_flag):
        assert isinstance(stri[0], str)
        res = [ord(stri[i]) if len(stri[i]) > 0 else 0 for i in range(len(stri))]
        for i, re in enumerate(res):
            if re == zero_flag:
                res[i] = 0
        return np.array(res)

    @staticmethod
    def _byte_to_str(byte):
        assert isinstance(byte, bytes)
        return byte.decode('utf-8')

    @staticmethod
    def _str_list_to_str(str_list):
        assert isinstance(str_list[0], str)
        return "".join(s_i for s_i in str_list)

    @staticmethod
    def _byte_to_int_all_disk(data, conf):
        res = list(map(RAID._byte_to_str, data))
        res = list(map(RAID._str_to_order_for_parity, res, [conf.char_order_for_zero for _ in range(len(res))]))
        return res

    def _int_data_to_string(self, data, non_zero_flag):
        data = np.transpose(np.array(data))
        data = np.reshape(data, [-1])
        if non_zero_flag:
            str = "".join(self.no_empty_chr(val) for val in data)
        else:
            str = "".join(chr(val) for val in data)
        return str

    @staticmethod
    def _int_data_to_chr(data):
        data = np.array(data).tolist()
        data = [list(map(chr, data_i)) for data_i in data]
        return data
