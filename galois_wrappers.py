# -*- coding: utf-8 -*-
"""
Created on Sat Nov  6 22:42:45 2021

@author: yipji
"""

import galois_functions as gf

def create_parities(list_of_drives, drive_ids=None, skip_P = False, skip_Q = False, store_as_chr=False):    
    
    if drive_ids == None:
        drive_list = []
             
        for drive_idx , drive_object in enumerate(list_of_drives):
            drive_id = drive_object.get_id()
            # drive_name = 'drive_'+ str(drive_id)
            drive_list.append([str(drive_id), drive_id])
        # drive_list = gf.assign_drive_ids(gf.drives_to_int(list_of_drives))
    
    else:
    
        if not len(list_of_drives)==len(drive_ids):
            raise Exception(f'List of drives must be the same length as drive ids. \n List of drives is length {len(list_of_drives)} \n drive_ids is length {len(drive_ids)}')
        
        drive_list = []
        count = 0
        for drive_idx , drive_object in enumerate(list_of_drives):
            drive_id = drive_object.get_id()
            drive_name = 'drive_'+drive_id
            drive_list.append([gf.convert_to_int(drive_name), drive_id])
        # for i in list_of_drives:
        #     drive_list.append([gf.convert_to_int(i), drive_ids[count]])
        #     count += 1
    if not skip_P:
        P = gf.P_encoder(drive_list)
    else:
        P = None
    
    if not skip_Q:
        Q = gf.Q_encoder(drive_list)
    else:
        Q = None
    # Storing P and Q as characters like the rest of the drives may lead to errors 
    # and an unecessary calculation step when converting back and forth  
    # Thus it is better if we store P and Q as int. 
    # However, if you really want to, this toggle is built here to convert everything back to chr
    if store_as_chr:
        P = gf.convert_to_chr(P)
        Q = gf.convert_to_chr(Q)
    
    P = gf.convert_to_chr(gf.convert_to_numpy(P))
    Q = gf.convert_to_chr(gf.convert_to_numpy(Q))
    return P, Q, drive_list #we output the drive list for accounting purposes, but mostly we expect this output to be ignored

def check_for_failures(drive_list, P, Q):
    
    P_check = gf.P_encoder(drive_list) == P
    Q_check = gf.Q_encoder(drive_list) == Q
    
    if P_check.all() and Q_check.all():
        return "No failures"
    else:
        return "At least one failure"
    

def galois_drive_recovery_wrapper(mode, remaining_drives = None, P = None, Q = None, missing_drive_id_1 = None, missing_drive_id_2 = None):
    '''
    ONE DRIVE LOST
    --------------
    
    case 1: loss of 1 data drive
        >>> recompute using P drive
        
    case 2: loss of P drive
        >>> recompute using remaining drives
        
    case 3: loss of Q drive
        >>> recompute using remaining drives
    
    TWO DRIVES LOST
    ---------------
    
    case 4: loss of 1 data drive and P drive
        >>> recompute missing data drive with Q drive
        >>> recompute P drive
        
    case 5: loss of 1 data drive and Q drive
        >>> recompute missing data drive with P drive
        >>> recompute Q drive
        
    case 6: loss of 2 data drives
        >>> recompute using P, Q and remaining data drives using the two_drives_lost function
        
    case 7: loss of P and Q drives
        >>> recompute P and Q drives
    
    '''
    if mode == 1:
        return gf.P_decoder(P, remaining_drives, missing_drive_id_1)
    
    elif mode == 2:
        return gf.P_encoder(remaining_drives)
    
    elif mode == 3:
        return gf.Q_encoder(remaining_drives)
    
    elif mode == 4:
        fixed_drive = gf.Q_decoder(Q, remaining_drives, missing_drive_id_1)
        remaining_drives.append(fixed_drive)
        P = gf.P_encoder(remaining_drives)
        return fixed_drive, P
    
    elif mode == 5:
        fixed_drive = gf.P_decoder(Q, remaining_drives, missing_drive_id_1)
        remaining_drives.append(fixed_drive)
        P = gf.Q_encoder(remaining_drives)
        return fixed_drive, Q
    
    elif mode == 6:
        return gf.two_drives_lost(P, Q, remaining_drives, missing_drive_id_1, missing_drive_id_2)
    
    elif mode == 7:
        P = gf.P_encoder(remaining_drives)
        Q = gf.Q_encoder(remaining_drives)
        return P, Q



if __name__ == '__main__':
    d0 = ['l33t','1234']
    d1 = ['0984','asdw']
    d2 = ['kzje','2f4a']
    
    list_of_drives = [d0,d1,d2]
    P1, Q1, DL1 = create_parities(list_of_drives, [0,1,2])
    
    P2, Q2, DL2 = create_parities(list_of_drives)
    
    print('Check that the parity creation function is working')
    print('Are the calculated Ps equal?')
    print(P1==P2)
    print('Are the calculated Qs equal?')
    print(Q1==Q2)
    print('Are the Drive Lists equal?')
    print(DL1==DL2)
    
    
    print('\n Does skipping work?')
    Px = create_parities(list_of_drives, [0,1,2], skip_P = True)
    Qx = create_parities(list_of_drives, [0,1,2], skip_Q = True)
    xx = create_parities(list_of_drives, [0,1,2], True, True)
    print(Px[0])
    print(Qx[1])
    print(xx[0:2])

    print('\n Does it store as char?')
    Pi, Qi, _ = create_parities(list_of_drives)
    Pc, Qc, _ = create_parities(list_of_drives, store_as_chr = True)
    print(Pi, Pc, gf.convert_to_int(Pc))
    print(Qi, Qc, gf.convert_to_int(Qc))
    
    
    print('\n \n Check for failures')
    broken_drives = DL1.copy()
    broken_drives.pop(1)
    print('Test1: one broken drive')
    print(f' test returns: {check_for_failures(broken_drives, P1, Q1)}')
    print('Test2: no broken drives')
    print(f' test returns: {check_for_failures(DL1, P1, Q1)}')