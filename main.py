from functools import wraps
import sys
import os
import sys

# ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
# sys.path.append(ROOT_DIR)
# PAR_PATH = os.path.abspath(os.path.join(ROOT_DIR, os.pardir))
# sys.path.append(PAR_PATH)

from RAID_File.raid_6_v2 import RAID
from fileObject import FileObject
from diskObject import DiskObject
import logging
import numpy as np
from galois_wrappers_v2 import galois_drive_recovery
import galois_functions_v2 as gf

logging.basicConfig(filename='disk.log', level=logging.INFO)

np.random.seed(1337)

RAID_settings = {
    # 'total_num_disk' : (2+8), #normal + parity disks
    'num_parity_disk': 2, #1 parity # 1 RS
    'num_normal_disk' : 8, # 8 data disks
    'size_of_disk': 16, #should be multiple of stripe size  and size_of_disk * num_normal disk > size_of_file
    'size_of_file': (16*8), #size of all the data to be generated which will be stripped and allocated into the #n disks
    'stripe_size' : 4,
    # 'data_disks' : (16 * 8),  #num_normal_disk * size_of_disk. This is the size of the mega file to be stripped
    # 'root_dir' : '/Users/xavier/Documents/NTU/CE7490/Assignment_2/RAID-6/C_drive',
    # 'root_dir' : '/Users/yipji/Offline Documents/Git Folder/CE7490_Raid6',
    'root_dir': os.getcwd() + '\\C_drive'
}

#Helper functions for unit tests
def after_recovery(raid_6):
    print('\n after recovery')
    print(raid_6.check_for_failure())
    if raid_6.check_for_failure() == "No failures":
        print('PASS')
    else:
        raise Exception('Test Failed')
    return
def before_recovery(raid_6, toggle = None, silence_header = False):
    if not silence_header:
        print("\n before recovery")
    print(raid_6.check_for_failure())
    if toggle == None:
        if raid_6.check_for_failure() == "At least one failure":
            print('PASS')
        else:
            raise Exception('Test Failed')
    elif toggle == 'p':
        if raid_6.check_for_failure() == "P disk failure":
            print('PASS')
        else:
            raise Exception('Test Failed')
    elif toggle == 'q':
        if raid_6.check_for_failure() == "Q disk failure":
            print('PASS')
        else:
            raise Exception('Test Failed')

if __name__ == '__main__':

    logging.info("Start")

    #init raid controller for the disks
    raid_6 = RAID(root_dir = RAID_settings['root_dir'], 
                  num_normal_disk = RAID_settings['num_normal_disk'], 
                  size_of_disk = RAID_settings['size_of_disk'], 
                  stripe_size = RAID_settings['stripe_size'] )
   
    #init temp data_disk to store file
    temp_data_disk = DiskObject(disk_dir=RAID_settings['root_dir'], disk_id=-9, size=RAID_settings['size_of_file'], stripe_size = RAID_settings['stripe_size'], type='data')
    
    #create a file to put in the temp data disk
    file = FileObject()
    
     # Random Generate some files and store into the data disks
    file.generate_random_data(data_size=RAID_settings['size_of_file'])
    
    #store file into temp data disk
    temp_data_disk.write(data=file.get_file_content())
    
    # Load data from data disk into RAID 6
    logging.info("START : Write to RAID 6")
    
    msg = raid_6.striping_data_blocks_to_raid_disks(temp_data_disk.get_data_block())
    print(msg)
    logging.info("END : Write to RAID 6")
        
    print('------------START UNIT TESTS---------------')
    print(raid_6.compute_Q(write = True))
    print(raid_6.compute_P(write = True))
    print('Test if the P and Q drives have been computed and stored correctly')
    print(raid_6.check_for_failure())
    if raid_6.check_for_failure() == "No failures":
        print('PASS')
    else:
        raise Exception('Test Failed')
    
    #Manual disk corruption settings
    original_disks = raid_6.get_disk_list().copy()
    
    pop_1 = 6
    broken_1_disks = original_disks.copy()
    poped_1 = broken_1_disks.pop(pop_1)
    missing_disk_id_1 = poped_1.get_id()
    
    pop_2 = 3
    broken_2_disks = broken_1_disks.copy()
    poped_2 = broken_2_disks.pop(pop_2)
    missing_disk_id_2 = poped_2.get_id()
    
    
    print('-------------------')
    print('\n Test if we correctly detect the failure')
    raid_6.disk_list = broken_1_disks
    print(raid_6.check_for_failure())
    if raid_6.check_for_failure() == "At least one failure":
        print('PASS')
    else:
        raise Exception('Test Failed')
        
    print('-------------------')

    print('\n Test if we can replace the original disks')
    raid_6.disk_list = original_disks
    print(raid_6.check_for_failure())
    if raid_6.check_for_failure() == "No failures":
        print('PASS')
    else:
        raise Exception('Test Failed')
        
    print('-------------------')
    
    
    print('\n Test if the lost disk is recoverable without use of wrapper')
    raid_6.disk_list = broken_1_disks.copy()
    before_recovery(raid_6)
    
    print('\n recovery') 
    rD = gf.P_decoder(P = gf.drive_to_gf(raid_6.get_P()), 
                      remaining_disks = broken_1_disks, 
                      missing_disk_id = missing_disk_id_1)
    rD = gf.convert_to_chr(gf.convert_to_numpy(rD))
    print('recovered drive is')
    print(rD)
    print('original drive was')
    print(poped_1.get_data_block())
    if rD == poped_1.get_data_block():
        print("PASS")
    else:
        raise Exception('Test Failed')
        
    raid_6.add_new_data_disk(rD,missing_disk_id_1)    
    after_recovery(raid_6)
        
    print('-------------------')    
    
    print('\n TEST FAILURE MODE 1: loss of 1 data drive')
    
    raid_6.disk_list = broken_1_disks.copy()
    before_recovery(raid_6)
        
    print('\n recovery') 
    msg = galois_drive_recovery(raid_6 = raid_6, 
                                mode = 1, 
                                P = gf.drive_to_gf(raid_6.get_P()), 
                                missing_disk_id_1 = missing_disk_id_1
                                )
    print(msg)    
    after_recovery(raid_6)
        
    print('-------------------') 
    
    print('\n TEST FAILURE MODE 2: loss of P drive')
    raid_6.p_disk = None
    before_recovery(raid_6, 'p')
   
    
    print('\n recovery')         
    msg = galois_drive_recovery(raid_6 = raid_6, 
                                mode = 2, 
                                Q = gf.drive_to_gf(raid_6.get_Q()), 
                                )
    print(msg)    
    after_recovery(raid_6)
    
    print('-------------------') 
    
    print('\n TEST FAILURE MODE 3: loss of Q drive')
    raid_6.q_disk = None
    before_recovery(raid_6, 'q')
    
    print('\n recovery')    
    msg = galois_drive_recovery(raid_6 = raid_6, 
                                mode = 3, 
                                P = gf.drive_to_gf(raid_6.get_P()), 
                                )
    print(msg)
    after_recovery(raid_6)
    
    print('-------------------')    
    
    print('\n TEST FAILURE MODE 4: loss of 1 data drive and P drive')
    
    raid_6.disk_list = broken_1_disks.copy()    
    before_recovery(raid_6)
    
    raid_6.p_disk = None
    before_recovery(raid_6, 'p', True)
    
    print('\n recovery')    
    msg = galois_drive_recovery(raid_6 = raid_6, 
                                mode = 4, 
                                Q = gf.drive_to_gf(raid_6.get_Q()),
                                missing_disk_id_1 = missing_disk_id_1,
                                )
    print(msg)
    after_recovery(raid_6)
    
    print('-------------------')        

    print('\n TEST FAILURE MODE 5: loss of 1 data drive and Q drive')
    
    raid_6.disk_list = broken_1_disks.copy() 
    before_recovery(raid_6)
    
    raid_6.q_disk = None
    before_recovery(raid_6, 'q', True)
    
    print('\n recovery')    
    msg = galois_drive_recovery(raid_6 = raid_6, 
                                mode = 5, 
                                P = gf.drive_to_gf(raid_6.get_P()),
                                missing_disk_id_1 = missing_disk_id_1,
                                )
    print(msg)
    after_recovery(raid_6)
    
    print('-------------------')      
    
    print('\n TEST FAILURE MODE 6: loss of 2 data drives')
    
    raid_6.disk_list = broken_2_disks.copy() 
    before_recovery(raid_6)
    
    print('\n recovery')    
    msg = galois_drive_recovery(raid_6 = raid_6, 
                                mode = 6, 
                                P = gf.drive_to_gf(raid_6.get_P()),
                                Q = gf.drive_to_gf(raid_6.get_Q()),
                                missing_disk_id_1 = missing_disk_id_1,
                                missing_disk_id_2 = missing_disk_id_2,
                                )
    print(msg)
    after_recovery(raid_6)
    
    print('-------------------')      
    
    print('\n TEST FAILURE MODE 7: loss of P and Q drives')
    
    raid_6.q_disk = None
    before_recovery(raid_6, 'q')
    
    raid_6.p_disk = None
    before_recovery(raid_6, 'p', True)
        
    print('\n recovery')    
    msg = galois_drive_recovery(raid_6 = raid_6, 
                                mode = 7, 
                                )
    print(msg)
    after_recovery(raid_6)
    
    print('---------TESTS COMPLETED----------') 
    logging.info("Stop")
    
    
    
    


    


    # logging.log_str("START : Read corrupted data")

    # data = raid_6.read_all_data_disks()
    # raid_6.check_corruption(disk_data_in_int=data)

    # logging.log_str("START : Recovery of data")
    # # Start to do the recover test
    # corrupted_disk_list = [3, 4]
    # for disk_id in corrupted_disk_list:
    #     with open(file=os.path.join(raid_6.disk_list[disk_id].disk_path, 'data'), mode='w') as f:
    #         f.write("")
    #         logging.log_str('Disk {}\'s data is erased'.format(disk_id))

    # raid_6.recover_disk(corrupted_disk_index=(3, 4))
    # raid_6.read_from_disk_and_generate_data()

    # # Update one char in file and re-generate
    # logging.log_str("START : UPDATE")

    # file.update(idx=0, new_data='t')
    # data_disk.write(id=data_disk.get_id, data=file.get_file_content)
    # data_block_list = data_disk.get_data_block(stripe_size=RAID_settings['stripe_size'])
    # for i, new_data, old_data in zip(range(len(data_block_list)), data_block_list, raid_6.data_block_list):
    #     if new_data != old_data:
    #         raid_6.update_data(block_global_index=i, new_data_block=new_data)
    #         break

    # raid_6.read_from_disk_and_generate_data()

    # # Update one char in file and re-generate

    # file.update(idx=1, new_data='d')
    # data_disk.write(id=data_disk.get_id, data=file.get_file_content)
    # data_block_list = data_disk.get_data_block(stripe_size=RAID_settings['stripe_size'])
    # for i, new_data, old_data in zip(range(len(data_block_list)), data_block_list, raid_6.data_block_list):
    #     if new_data != old_data:
    #         raid_6.update_data(block_global_index=i, new_data_block=new_data)
    #         break

    # raid_6.read_from_disk_and_generate_data()



