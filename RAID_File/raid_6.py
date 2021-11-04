from galois import GF2
import numpy as np
import concurrent.futures
import math
from copy import deepcopy

GF256 = GF2(2**8)

class RAID(object):

    def __init__(self, disk_list, config, gf=None):
        super().__init__(6, disk_list)
        self.config = config
        assert self.raid_level == 6
        if not gf:
            self.gf = GF2(num_data_disk=self.config.data_disk_count,
                                  num_checksum=self.config.parity_disk_count)
        else:
            self.gf = gf
        self.encode_matrix = self._generate_encode_matrix()
        self.parity_int = None
        self.parity_char = None
        self.block_to_disk_map = None
        self.data_block_list = None

    def write_file(self, data_block_list):
        """
        Write the file to the disks concurrently, firstly computing the parity then concurrently write to all the disks
        :param data_block_list: a list contains the stripped data blocks
        :return: None
        """
        self.data_block_list = data_block_list
        data = self._split_block_into_data_disks(data_disks_n=self.config.data_disk_count,
                                                 data_block=data_block_list,
                                                 block_count_per_chunk=self.config.block_num_per_chunk)
        data_with_parity = np.concatenate([data, self.compute_parity(data=data)], axis=0)

        for disk, data in zip(self.disk_list, data_with_parity.tolist()):
            disk.write_to_disk(disk=disk, data="".join(self.no_empty_chr(val) for val in data), mode='w')

    def no_empty_chr(self, val):
        """
        convert a char to its order while convert '' to pre-defined number
        :param val: original char
        :return: a scalar
        """
        assert isinstance(val, str)
        if val == '':
            return chr(self.config.char_order_for_zero)
        else:
            return val

    def read_all_data_disks(self, corrupted_disk_index=()):
        """
        Read the disks concurrently to a numpy array.
        :return: Data from all the disks
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.disk_count) as executor:
            res = list(executor.map(Disk.read(), self.disk_list))

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
        self.parity_int, self.parity_char = self.gf.gen_parity(data=np.array(int_data))
        Logger.log_str(log_str='Get the parity:\n{}'.format(self.parity_int))
        return self.parity_char

    def check_corruption(self, disk_data_in_int):
        """
        Detect if single disk occurred silent corruption.
        :return: A boolean, True for failed, False for not.
        """
        new_parity, _ = self.gf.gen_parity(disk_data_in_int[0:self.config.data_disk_count])
        Logger.log_str('Check silent corruption\nNew parity is {}'.format(new_parity))
        Logger.log_str('Old parity is {}'.format(self.parity_int))
        res = np.bitwise_xor(np.array(self.parity_int), np.array(new_parity))
        if np.count_nonzero(res) == 0:
            Logger.log_str('No corruption')
        else:
            Logger.log_str('Exist corruption!!!', mode='error')
        pass

    def recover_disk(self, corrupted_disk_index=()):
        """
        Recover the data by using gaussian elimination
        :param corrupted_disk_index: a list contain the corrupted disk indexes
        :return: None
        """
        Logger.log_str(log_str='Corrupted disks detected: {}'.format(corrupted_disk_index))

        # Retrieve the good disks data: vector_e_new and corresponding encode matrix rows: matrix_a_new
        matrix_a_new, vector_e_new = self.gf.recover_matrix(mat_a=self.encode_matrix,
                                                            vec_e=self.read_all_data_disks(corrupted_disk_index),
                                                            corrupt_index=corrupted_disk_index)
        data_strip_count = vector_e_new.shape[1]
        new_data = []
        for i in range(data_strip_count):
            augmented_matrix = np.concatenate((matrix_a_new, np.reshape(vector_e_new[:, i], [-1, 1])), axis=1)
            # Gaussian elimination is carried out in a block by block manner
            new_data.append(self._gaussian_elimination(augmented_matrix))
        new_data = np.transpose(new_data)
        self.parity_int, self.parity_char = self.gf.gen_parity(new_data)
        Logger.log_str(log_str='Recovered disks: {}'.format(corrupted_disk_index))
        new_data = self._int_data_to_chr(data=new_data)
        data_with_parity = np.concatenate([new_data, self.parity_char], axis=0)
        # Write the recovered data to disks
        for i, disk, data in zip(range(self.config.disk_count), self.disk_list, data_with_parity.tolist()):
            if i in corrupted_disk_index:
                disk.write_to_disk(disk=disk, data="".join(self.no_empty_chr(val) for val in data), mode='w')
        Logger.log_str('Recovered data is written to disk')

    def update_data(self, block_global_index, new_data_block):
        """
        Update the file
        :param block_global_index: the block's index that need to be updated
        :param new_data_block: new data block
        :return: None
        """
        # First get the block position in the RAID 6

        disk_id, chuck_id = self.block_to_disk_map[block_global_index]
        self.data_block_list[block_global_index] = new_data_block
        str_data = self._byte_to_str(new_data_block)
        int_data = self._str_to_order(str_data)[0]

        # Generate the new parity, by only computing the block that is changed.

        parity_int, parity_char = self.gf.gen_parity(data=np.array(int_data).reshape([1, -1]))
        Logger.log_str(log_str='Get the parity:\n{}'.format(self.parity_int))
        parity_char = parity_char.reshape([-1])
        parity_int = parity_int.reshape([-1])

        # Update the parity (only for class attribute maintenance)
        for i in range(self.config.parity_disk_count):
            self.parity_int[i][chuck_id] = parity_int[i]
            self.parity_char[i][chuck_id] = parity_char[i]
        Logger.log_str(log_str='Get the updated parity:\n{}'.format(self.parity_int))

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
        disk.write_to_disk(disk=disk, data="".join(self.no_empty_chr(val) for val in new_res),
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

    def _generate_encode_matrix(self):
        """
        Get the encoding matrix from GF field
        :return: the matrix
        """
        return self.gf.gen_matrix_A()

    def _split_block_into_data_disks(self, data_disks_n, data_block, block_count_per_chunk):
        """
        Split the data block from logical disk into raid data disks
        :param data_disks_n: total number of data disks in raid 6
        :param data_block: data blocks from logical disk that will be stripped into raid 6
        :param block_count_per_chunk: assign how many data blocks to one data disk before moving to the next
        :return:
        """

        self.block_to_disk_map = [None for _ in range(len(data_block))]
        disk_index = 0
        data_disk_list = [[] for _ in range(data_disks_n)]
        for i, block_i in enumerate(data_block):
            data_disk_list[disk_index].append(self._str_to_order(block_i) if isinstance(block_i, str) else block_i)
            self.block_to_disk_map[i] = (disk_index, len(data_disk_list[disk_index]) - 1)
            if (i + 1) % block_count_per_chunk == 0:
                disk_index = (disk_index + 1) % data_disks_n

        padding_block = self.generate_padding_block(byte_length=len(data_block[0]))
        assert len(padding_block) == len(data_block[0])
        assert isinstance(padding_block, type(data_block[0]))
        data_block_per_disk = 0
        for data in data_disk_list:
            data_block_per_disk = max(data_block_per_disk, len(data))

        for index, data in enumerate(data_disk_list):
            if len(data) < data_block_per_disk:
                for _ in range(data_block_per_disk - len(data)):
                    data_disk_list[index].append(padding_block)
        for data in data_disk_list:
            assert len(data) == data_block_per_disk
        return np.array(data_disk_list)

    def read_from_disk_and_generate_data(self):
        """
        Read the data in data disks of RAID 6 and generate the original file content as a validation process
        :return: None
        """
        res = self.read_all_data_disks()
        res = [re.tolist() for re in res][0:self.config.data_disk_count]
        new_res = []
        for i, j in self.block_to_disk_map:
            new_res.append(res[i][j])
        Logger.log_str(
            'Data is {}'.format(self._int_data_to_string(new_res, non_zero_flag=False)))

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
    def _str_to_order(stri):
        assert isinstance(stri[0], str)
        res = [ord(stri[i]) if len(stri[i]) > 0 else 0 for i in range(len(stri))]
        return np.array(res)

    @staticmethod
    def generate_padding_block(byte_length):
        assert byte_length % 4 == 0
        return np.array(['' for _ in range(byte_length // 4)]).tostring()

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
        res = list(map(RAID_6._byte_to_str, data))
        res = list(map(RAID_6._str_to_order_for_parity, res, [conf.char_order_for_zero for _ in range(len(res))]))
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
