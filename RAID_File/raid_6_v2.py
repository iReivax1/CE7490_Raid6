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

            
   