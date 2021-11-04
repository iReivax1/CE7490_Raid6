import sys
import os
import sys

# ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
# sys.path.append(ROOT_DIR)
# PAR_PATH = os.path.abspath(os.path.join(ROOT_DIR, os.pardir))
# sys.path.append(PAR_PATH)

from RAID_File.raid_6 import RAID
from file import File
from partitions import DiskObject
import logging

logging.basicConfig(filename='disk.log', level=logging.INFO)

RAID_settings = {
    'total_num_disk' : (2+2),
    'num_normal_disk' : 2,
    'num_parity_disk': 2,
    'size_of_disk': 16, 
    'size_of_file': 8,#in bits
    'stripe_size' : 4,
    'data_disks' : (16 * 2),  #num_normal_disk * size_of_disk
    'root_dir' : '/Users/xavier/Documents/NTU/CE7490/Assignment_2/RAID-6/C_drive',
}

def main():

    logging.info("Start")
    all_disk = []
    for idx in range(RAID_settings['total_num_disk']):
        all_disk.append(DiskObject(dir=RAID_settings['root_dir'], id=idx, size=RAID_settings['size_of_disk'], type='data'))

    #store all the data as per normal, first 2 disk is normal
    data_disk = DiskObject(dir=RAID_settings['root_dir'], id=-1, size=RAID_settings['data_disks'], type='data')
    

    #init raid for the disks
    raid_6 = RAID(disk_list=all_disk)

    # Random Generate some files and store into the data disks
    file = File()
    file.generate_random_data(data_size=RAID_settings['size_of_file'])
    data_disk.write_to_disk(disk=data_disk, data=file.get_file_content)
    data_block_list = data_disk.get_data_block(stripe_size=RAID_settings['stripe_size'])

    # Load data from data disk into RAID 6
    logging.log_str("START : Write to RAID 6")

    raid_6.write_file(data_block_list=data_block_list)
    raid_6.read_from_disk_and_generate_data()

    logging.log_str("START : Read corrupted data")

    data = raid_6.read_all_data_disks()
    raid_6.check_corruption(disk_data_in_int=data)

    logging.log_str("START : Recovery of data")
    # Start to do the recover test
    corrupted_disk_list = [3, 4]
    for disk_id in corrupted_disk_list:
        with open(file=os.path.join(raid_6.disk_list[disk_id].disk_path, 'data'), mode='w') as f:
            f.write("")
            logging.log_str('Disk {}\'s data is erased'.format(disk_id))

    raid_6.recover_disk(corrupted_disk_index=(3, 4))
    raid_6.read_from_disk_and_generate_data()

    # Update one char in file and re-generate
    logging.log_str("START : UPDATE")

    file.update(idx=0, new_data='t')
    data_disk.write(id=data_disk.get_id, data=file.get_file_content)
    data_block_list = data_disk.get_data_block(stripe_size=RAID_settings['stripe_size'])
    for i, new_data, old_data in zip(range(len(data_block_list)), data_block_list, raid_6.data_block_list):
        if new_data != old_data:
            raid_6.update_data(block_global_index=i, new_data_block=new_data)
            break

    raid_6.read_from_disk_and_generate_data()

    # Update one char in file and re-generate

    file.update(idx=1, new_data='d')
    data_disk.write(id=data_disk.get_id, data=file.get_file_content)
    data_block_list = data_disk.get_data_block(stripe_size=RAID_settings['stripe_size'])
    for i, new_data, old_data in zip(range(len(data_block_list)), data_block_list, raid_6.data_block_list):
        if new_data != old_data:
            raid_6.update_data(block_global_index=i, new_data_block=new_data)
            break

    raid_6.read_from_disk_and_generate_data()


if __name__ == '__main__':
    main()
