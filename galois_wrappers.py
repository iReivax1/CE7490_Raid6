# -*- coding: utf-8 -*-
"""
Created on Sat Nov  6 22:42:45 2021

@author: yipji
"""

import galois_functions as gf
import warnings
import time

def galois_drive_recovery(raid_6, mode, remaining_disks = None, P = None, Q = None, missing_disk_id_1 = None, missing_disk_id_2 = None):
    '''
    ONE DRIVE LOST
    --------------
    
    case 1: loss of 1 data drive
        >>> recompute using P drive
        RETURNS: [data, id]
        
    case 2: loss of P drive
        >>> recompute using remaining drives
        RETURNS: P
        
    case 3: loss of Q drive
        >>> recompute using remaining drives
        RETURNS: Q
    
    TWO DRIVES LOST
    ---------------
    
    case 4: loss of 1 data drive and P drive
        >>> recompute missing data drive with Q drive
        >>> recompute P drive
        RETURNS: [data, id], P
        
    case 5: loss of 1 data drive and Q drive
        >>> recompute missing data drive with P drive
        >>> recompute Q drive
        RETURNS: [data, id], Q
        
    case 6: loss of 2 data drives
        >>> recompute using P, Q and remaining data drives using the two_drives_lost function
        RETURNS: [data, id], [data, id]
        
        
    case 7: loss of P and Q drives
        >>> recompute P and Q drives
        RETURNS: P, Q
    
    '''
    
    ##Check if the raid array is broken before proceeding
    tic = time.perf_counter()
    
    if raid_6.check_for_failure() == "No failures":
        raise Exception('the raid_6 array is not broken')
    
    #We assume that whatever disk is left in the array is broken 
    if remaining_disks == None:
        # print('WARNING: no "remaining disks" provided, using disk_list from raid_6')
        remaining_disks = raid_6.disk_list.copy()
    
    if mode == 1:
        rD = gf.P_decoder(P, remaining_disks, missing_disk_id_1)
        rD = gf.convert_to_chr(gf.convert_to_numpy(rD))
        raid_6.add_new_data_disk(rD, missing_disk_id_1)
        return f"Disk id {missing_disk_id_1} recovered and restored." + f"\nTook {time.perf_counter()-tic:0.4f} seconds"
    
    elif mode == 2:
        raid_6.p_disk = raid_6.create_disk(-1,'P')
        return raid_6.compute_P(write=True) + f"\nTook {time.perf_counter()-tic:0.4f} seconds"
    
    elif mode == 3:
        raid_6.q_disk = raid_6.create_disk(-2,'Q')
        return raid_6.compute_Q(write=True) + f"\nTook {time.perf_counter()-tic:0.4f} seconds"
    
    elif mode == 4:
        rD = gf.Q_decoder(Q, remaining_disks, missing_disk_id_1)
        rD = gf.convert_to_chr(gf.convert_to_numpy(rD))
        raid_6.add_new_data_disk(rD, missing_disk_id_1)
        
        raid_6.p_disk = raid_6.create_disk(-1,'P')
        msg = raid_6.compute_P(write=True)
        return f"Disk id {missing_disk_id_1} recovered and restored; in addition " + msg + f"\nTook {time.perf_counter()-tic:0.4f} seconds"
    
    elif mode == 5:
        rD = gf.P_decoder(P, remaining_disks, missing_disk_id_1)
        rD = gf.convert_to_chr(gf.convert_to_numpy(rD))
        raid_6.add_new_data_disk(rD, missing_disk_id_1)
        
        raid_6.q_disk = raid_6.create_disk(-2,'Q')
        msg = raid_6.compute_Q(write=True)
        return f"Disk id {missing_disk_id_1} recovered and restored; in addition " + msg + f"\nTook {time.perf_counter()-tic:0.4f} seconds"
    
    elif mode == 6:
        rD1, rD2 = gf.two_drives_lost(P, Q, remaining_disks, missing_disk_id_1, missing_disk_id_2)
        
        rD1 = gf.convert_to_chr(gf.convert_to_numpy(rD1))
        raid_6.add_new_data_disk(rD1, missing_disk_id_1)
        
        rD2 = gf.convert_to_chr(gf.convert_to_numpy(rD2))
        raid_6.add_new_data_disk(rD2, missing_disk_id_2)
        
        return f"Disk id {missing_disk_id_1} and {missing_disk_id_2} recovered and restored" + f"\nTook {time.perf_counter()-tic:0.4f} seconds"
    
    elif mode == 7:
        raid_6.p_disk = raid_6.create_disk(-1,'P')
        msg_P = raid_6.compute_P(write=True)
        
        raid_6.q_disk = raid_6.create_disk(-2,'Q')
        msg_Q = raid_6.compute_Q(write=True)
        return msg_P + 'and; \n ' + msg_Q + f"\nTook {time.perf_counter()-tic:0.4f} seconds"
