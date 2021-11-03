import sys
import os
import sys

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(CURRENT_PATH)
PAR_PATH = os.path.abspath(os.path.join(CURRENT_PATH, os.pardir))
sys.path.append(PAR_PATH)

from src.raid.raid_6 import RAID_6
from src.file import File
from src.disk import Disk
from src.util import Configuration, Logger


def main():

    # Set up the configuration

    conf = Configuration()
    conf.log_out()
    Logger.log_str("-----------------Set up the RAID 6 system-----------------")

    # Set up the RAID 6 disks and RAID 6 disk controller

    disk_list = [Disk(disk_path=conf.disk_dir, id=i, disk_size=conf.disk_size) for i in range(conf.disk_count)]
    raid_6 = RAID_6(disk_list=disk_list,
                    config=conf)

    # Set up a logical disk to store the original data files

    logical_disk = Disk(disk_path=conf.disk_dir, id=-1, disk_size=conf.logical_disk_size)

    # Random Generate some files and store into logical disk

    file = File()
    file.random_generate_string(data_size=conf.random_file_size)
    logical_disk.write_to_disk(disk=logical_disk, data=file.file_content)
    data_block_list = logical_disk.set_up_data_block_list(block_size=conf.block_size)

    # Load the data block from logical disk into RAID 6
    Logger.log_str("-----------------Write the file to RAID 6-----------------")

    raid_6.write_file(data_block_list=data_block_list)
    raid_6.read_from_disk_and_generate_data()

    Logger.log_str("-----------------Test silent corruption-----------------")

    # Start the test of raid 6
    data = raid_6.read_all_data_disks()
    raid_6.check_corruption(disk_data_in_int=data)

    Logger.log_str("-----------------Test data recovery-----------------")
    # Start to do the recover test
    corrupted_disk_list = (6, 7)
    for disk_id in corrupted_disk_list:
        with open(file=os.path.join(raid_6.disk_list[disk_id].disk_path, 'data'), mode='w') as f:
            f.write("")
            Logger.log_str('Disk {}\'s data is erased'.format(disk_id))

    raid_6.recover_disk(corrupted_disk_index=(6, 7))
    raid_6.read_from_disk_and_generate_data()

    # Update one char in file and re-generate
    Logger.log_str("-----------------Test data update-----------------")

    file.update(index=0, new_char='t')
    logical_disk.write_to_disk(disk=logical_disk, data=file.file_content)
    data_block_list = logical_disk.set_up_data_block_list(block_size=conf.block_size)
    for i, new_data, old_data in zip(range(len(data_block_list)), data_block_list, raid_6.data_block_list):
        if new_data != old_data:
            raid_6.update_data(block_global_index=i, new_data_block=new_data)
            break

    raid_6.read_from_disk_and_generate_data()

    # Update one char in file and re-generate

    file.update(index=1, new_char='d')
    logical_disk.write_to_disk(disk=logical_disk, data=file.file_content)
    data_block_list = logical_disk.set_up_data_block_list(block_size=conf.block_size)
    for i, new_data, old_data in zip(range(len(data_block_list)), data_block_list, raid_6.data_block_list):
        if new_data != old_data:
            raid_6.update_data(block_global_index=i, new_data_block=new_data)
            break

    raid_6.read_from_disk_and_generate_data()


if __name__ == '__main__':
    main()
