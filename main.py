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

# logging.basicConfig(filename='disk.log', level=logging.INFO)
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()
logger.addHandler(logging.FileHandler('unit_test.log', 'a'))
logging.info = logger.info

np.random.seed(1337)

RAID_settings = {
    # 'total_num_disk' : (2+8), #normal + parity disks
    'num_normal_disk' : 8, # 8 data disks
    'num_parity_disk': 2, #1 parity # 1 RS
    'size_of_disk': 16, #should be multiple of stripe size  and size_of_disk * num_normal disk > size_of_file
    'size_of_file': (8*4), #size of all the data to be generated which will be stripped and allocated into the #n disks
    'stripe_size' : 4,
    'data_disks' : (16 * 8),  #num_normal_disk * size_of_disk. This is the size of the mega file to be stripped
    # 'root_dir' : '/Users/xavier/Documents/NTU/CE7490/Assignment_2/RAID-6/C_drive',
    # 'root_dir' : '/Users/yipji/Offline Documents/Git Folder/CE7490_Raid6',
    'root_dir': os.getcwd() + '\\C_drive',
    'disk_failure_1': 6,
    'disk_failure_2': 3,
}

# Helper functions for unit tests


def after_recovery(raid_6):
    logging.info('\n after recovery')
    logging.info(raid_6.check_for_failure())
    if raid_6.check_for_failure() == "No failures":
        logging.info('PASS')
    else:
        raise Exception('Test Failed')
    return


def before_recovery(raid_6, toggle=None, silence_header=False):
    if not silence_header:
        logging.info("\n before recovery")
    logging.info(raid_6.check_for_failure())
    if toggle == None:
        if raid_6.check_for_failure() == "At least one failure":
            logging.info('PASS')
        else:
            raise Exception('Test Failed')
    elif toggle == 'p':
        if raid_6.check_for_failure() == "P disk failure":
            logging.info('PASS')
        else:
            raise Exception('Test Failed')
    elif toggle == 'q':
        if raid_6.check_for_failure() == "Q disk failure":
            logging.info('PASS')
        else:
            raise Exception('Test Failed')

def check_striping(raid_6):

    for disk in raid_6.get_disk_list():
        data = disk.read()
        logging.info(data)



if __name__ == '__main__':

    logging.info("Start")

    #init raid controller for the disks
    raid_6 = RAID(root_dir = RAID_settings['root_dir'], 
                  num_normal_disk = RAID_settings['num_normal_disk'], 
                  size_of_disk = RAID_settings['size_of_disk'], 
                  stripe_size = RAID_settings['stripe_size'] )
    # Random Generate some files and store into the data disks
    
    temp_data_disk = DiskObject(disk_dir=RAID_settings['root_dir'], disk_id=-9, size=RAID_settings['data_disks'], stripe_size = RAID_settings['stripe_size'], type='data')
    
    #create a file to put in the temp data disk
    file = FileObject()
    file.generate_random_data(data_size=RAID_settings['data_disks'])
    
    #store file into temp data disk
    temp_data_disk.write(data=file.get_file_content())
    

    # Load data from data disk into RAID 6
    logging.info("START : Write to RAID 6")
    
    msg = raid_6.striping_data_blocks_to_raid_disks(temp_data_disk.get_data_block())
    logging.info(msg)

        
    logging.info('------------START UNIT TESTS---------------')
    logging.info(raid_6.compute_Q(write = True))
    logging.info(raid_6.compute_P(write = True))
    logging.info('Test if the P and Q drives have been computed and stored correctly')
    logging.info(raid_6.check_for_failure())
    if raid_6.check_for_failure() == "No failures":
        logging.info('PASS')
    else:
        raise Exception('Test Failed')

    # Manual disk corruption settings
    original_disks = raid_6.get_disk_list().copy()

    pop_1 = RAID_settings['disk_failure_1']
    # pop_1 = 6
    broken_1_disks = original_disks.copy()
    poped_1 = broken_1_disks.pop(pop_1)
    missing_disk_id_1 = poped_1.get_id()

    # pop_2 = 3
    pop_2 = RAID_settings['disk_failure_2']
    broken_2_disks = broken_1_disks.copy()
    poped_2 = broken_2_disks.pop(pop_2)
    missing_disk_id_2 = poped_2.get_id()

    logging.info('-------------------')
    logging.info('\n Test if we correctly detect the failure')
    raid_6.disk_list = broken_1_disks
    logging.info(raid_6.check_for_failure())
    if raid_6.check_for_failure() == "At least one failure":
        logging.info('PASS')
    else:
        raise Exception('Test Failed')

    logging.info('-------------------')

    logging.info('\n Test if we can replace the original disks')
    raid_6.disk_list = original_disks
    logging.info(raid_6.check_for_failure())
    if raid_6.check_for_failure() == "No failures":
        logging.info('PASS')
    else:
        raise Exception('Test Failed')

    logging.info('-------------------')

    logging.info('\n Test if the lost disk is recoverable without use of wrapper')
    raid_6.disk_list = broken_1_disks.copy()
    before_recovery(raid_6)

    logging.info('\n recovery')
    rD = gf.P_decoder(P=gf.drive_to_gf(raid_6.get_P()),
                      remaining_disks=broken_1_disks,
                      missing_disk_id=missing_disk_id_1)
    rD = gf.convert_to_chr(gf.convert_to_numpy(rD))
    logging.info('recovered drive is')
    logging.info(rD)
    logging.info('original drive was')
    logging.info(poped_1.get_data_block())
    if rD == poped_1.get_data_block():
        logging.info("PASS")
    else:
        raise Exception('Test Failed')

    raid_6.add_new_data_disk(rD, missing_disk_id_1)
    after_recovery(raid_6)

    logging.info('-------------------')

    logging.info('\n TEST FAILURE MODE 1: loss of 1 data drive')

    raid_6.disk_list = broken_1_disks.copy()
    before_recovery(raid_6)

    logging.info('\n recovery')
    msg = galois_drive_recovery(raid_6=raid_6,
                                mode=1,
                                P=gf.drive_to_gf(raid_6.get_P()),
                                missing_disk_id_1=missing_disk_id_1
                                )
    logging.info(msg)
    after_recovery(raid_6)

    logging.info('-------------------')

    logging.info('\n TEST FAILURE MODE 2: loss of P drive')
    raid_6.p_disk = None
    before_recovery(raid_6, 'p')

    logging.info('\n recovery')
    msg = galois_drive_recovery(raid_6=raid_6,
                                mode=2,
                                Q=gf.drive_to_gf(raid_6.get_Q()),
                                )
    logging.info(msg)
    after_recovery(raid_6)

    logging.info('-------------------')

    logging.info('\n TEST FAILURE MODE 3: loss of Q drive')
    raid_6.q_disk = None
    before_recovery(raid_6, 'q')

    logging.info('\n recovery')
    msg = galois_drive_recovery(raid_6=raid_6,
                                mode=3,
                                P=gf.drive_to_gf(raid_6.get_P()),
                                )
    logging.info(msg)
    after_recovery(raid_6)

    logging.info('-------------------')

    logging.info('\n TEST FAILURE MODE 4: loss of 1 data drive and P drive')

    raid_6.disk_list = broken_1_disks.copy()
    before_recovery(raid_6)

    raid_6.p_disk = None
    before_recovery(raid_6, 'p', True)

    logging.info('\n recovery')
    msg = galois_drive_recovery(raid_6=raid_6,
                                mode=4,
                                Q=gf.drive_to_gf(raid_6.get_Q()),
                                missing_disk_id_1=missing_disk_id_1,
                                )
    logging.info(msg)
    after_recovery(raid_6)

    logging.info('-------------------')

    logging.info('\n TEST FAILURE MODE 5: loss of 1 data drive and Q drive')

    raid_6.disk_list = broken_1_disks.copy()
    before_recovery(raid_6)

    raid_6.q_disk = None
    before_recovery(raid_6, 'q', True)

    logging.info('\n recovery')
    msg = galois_drive_recovery(raid_6=raid_6,
                                mode=5,
                                P=gf.drive_to_gf(raid_6.get_P()),
                                missing_disk_id_1=missing_disk_id_1,
                                )
    logging.info(msg)
    after_recovery(raid_6)

    logging.info('-------------------')

    logging.info('\n TEST FAILURE MODE 6: loss of 2 data drives')

    raid_6.disk_list = broken_2_disks.copy()
    before_recovery(raid_6)

    logging.info('\n recovery')
    msg = galois_drive_recovery(raid_6=raid_6,
                                mode=6,
                                P=gf.drive_to_gf(raid_6.get_P()),
                                Q=gf.drive_to_gf(raid_6.get_Q()),
                                missing_disk_id_1=missing_disk_id_1,
                                missing_disk_id_2=missing_disk_id_2,
                                )
    logging.info(msg)
    after_recovery(raid_6)

    logging.info('-------------------')

    logging.info('\n TEST FAILURE MODE 7: loss of P and Q drives')

    raid_6.q_disk = None
    before_recovery(raid_6, 'q')

    raid_6.p_disk = None
    before_recovery(raid_6, 'p', True)

    logging.info('\n recovery')
    msg = galois_drive_recovery(raid_6=raid_6,
                                mode=7,
                                )
    logging.info(msg)
    after_recovery(raid_6)

    logging.info('---------TESTS COMPLETED----------')
    logging.info("Stop")
    logging.shutdown()
