# -*- coding: utf-8 -*-
"""
Created on Wed Nov  3 15:18:37 2021

@author: yipji
"""

import numpy as np

import galois

from coprimes_of_255 import coprimes_of_255

GF256 = galois.GF(2**8)

def convert_to_int(string):
    '''
    The purpose of this function is to convert a list of strings into a list of integers using the ord() function
    This list of strings represent a drive
    Each string is a file
    The list must not be nested. i.e. it should be in the form ['abcd', '1234', 'a2c4']
    '''
    if not isinstance(string, list):
        raise Exception(f'Drive should be a list, recieved a {type(string)}')
    
    file = []
    for i in string:
        unit = []
        for k in i:
            unit.append(ord(k))
        file.append(unit)
    return file


def drives_to_int(list_of_drives):
    '''
    The purpose of this function is to convert a list of drives into integers through recursion
    Each drive consists of a list of strings
    Each string represents a file
    '''
    
    drives = []
    
    arr = np.array(list_of_drives)
    if bool(arr.ndim > 1):
        for i in list_of_drives:
            drives.append(drives_to_int(i))
            # print(bool(np.array(i).ndim > 1))
    else:
        # print(list_of_drives)
        drives = convert_to_int(list_of_drives)
    
    return drives

def convert_to_chr(array):
    '''
    The purpose of this function is to convert a numpy array into characters 
    '''
    file = []
    for i in array:
        unit = ""
        for k in i:
            unit += chr(k)
        file.append(unit)
    return file

def convert_to_numpy(galois):
    '''
    The purpose of this function is to convert a galois field arry back into a numpy array
    '''
    file = []
    for i in galois:
        unit = []
        for k in i:
            unit.append(int(k))
        file.append(unit)
    return file

def assign_drive_ids(list_of_drives):
    '''
    This function assigns drive ids to a list of drives for galois computations
    '''
    drive_id = 0
    drive_list = []
    for i in list_of_drives:
        drive_list.append([i,drive_id])
        drive_id += 1
    return drive_list

def drive_to_gf(drive):
    '''
    this function expects a list of non-negative integers of arbitary length, where each integer <=255
    '''
    GF = galois.GF(2**8)
    return GF(drive)

def drive_encoder(drive, drive_ids):
    '''
    file: a list of non-negative integers of arbitary length, where each integer <=255
    drive_ids: the unique ids associated with the drive in the range of [0,255]
    returns: the GF encoding for the drive, multiple GF encodings will be summed to form the Q backup drive
    '''
    GF = galois.GF(2**8)
    g = GF(2)
    cp255 = coprimes_of_255()
    i = cp255[drive_ids]
    m = drive_to_gf(drive)
    q = (g**i)*m
    return q

def Q_encoder(drive_list):
    '''
    Parameters
    ----------
    drive_list : The value of the list of drives to be backed up. 
    **NOTE** - The drive_list should be in the format [drive, drive_id]
    where drive is a list of integers; and
    drive_id is a single integer

    Returns
    -------
    Q : The values for the Q drive

    '''
    
    Q = GF256(0)
    
    for drive, dn in drive_list:

        enc = drive_encoder(drive, dn)

        Q = Q+enc
        
    return Q

def P_encoder(drive_list):
    '''
    Parameters
    ----------
    drive_list : The value of the list of drives to be backed up. 
    **NOTE** - The drive_list should be in the format [drive, drive_id]
    where drive is a list of integers; and
    drive_id is a single integer

    Returns
    -------
    P : The values for the P drive

    '''
    
    P = GF256(0)
    
    for drive, _ in drive_list:

        enc = drive_to_gf(drive)

        P = P+enc
        
    return P


def Q_decoder(Q, remaining_drives, missing_drive_id):
    '''
    Parameters
    ----------
    This function is for the case where 1 drive fails
    
    Q : The values of the backup Q drive encoded as GF(2**8)
    remaining_drives : the values of the remaining drives
    **NOTE** - The drive_list should be in the format [drive, drive_id]
    where drive is a list of integers; and
    drive_id is a single integer
    missing_drive_id: This should be the drive id of the missing drive. It should be a single integer

    Returns
    -------
    The values of the missing drive

    '''
    GF = galois.GF(2**8)
    g = GF(2)
    cp255 = coprimes_of_255()
    i = cp255[missing_drive_id]
    
    Qx = Q_encoder(remaining_drives)
    D = (Q+Qx)/(g**i)
    return [convert_to_numpy(D), missing_drive_id]
    
def P_decoder(P, remaining_drives, missing_drive_id):
    '''
    This function is for the case where 1 data drive fails
    
    Parameters
    ----------
    Q : The values of the backup Q drive
    remaining_drives : the values of the remaining drives

    Returns
    -------
    The values of the missing drive

    '''
    GF = galois.GF(2**8)
    
    Px = P_encoder(remaining_drives)
    D = P-Px
    return [convert_to_numpy(D), missing_drive_id]

def two_drives_lost(P, Q, remaining_drives, missing_drive_id_1, missing_drive_id_2):
    '''
    The purpose of this function is to reconstruct the drives if two data drives go missing
    
    Parameters
    ----------
    P : The values stored in the P drive
    Q : The values stored in the  Q drive
    remaining_drives : The value of the remaining drives that were not lost
    missing_drive_id_1 : The drive id of the first drive that was corrupted
    missing_drive_id_2 : The drive id of the second drive that was corrupted

    Returns
    -------
    The reconstructed drives in the format: drive1, drive2
    '''
    
    #setting up the Galois parameters
    GF = galois.GF(2**8)
    g = GF(2)
    cp255 = coprimes_of_255()
    
    #precomputed constants
    x = cp255[missing_drive_id_1]
    y = cp255[missing_drive_id_2]
    
    gyx = g**y/g**x
    
    A = (gyx)/(gyx+GF(1))
    B = (g**(-x))/(gyx+GF(1))
    
    Pxy = P_encoder(remaining_drives)
    Qxy = Q_encoder(remaining_drives)
    
    #reconstruction
    Dx = (A*(P+Pxy)) + (B*(Q+Qxy))
    Dy = (P+Pxy) + Dx
    
    return [convert_to_numpy(Dx), missing_drive_id_1], [convert_to_numpy(Dy), missing_drive_id_2]

if __name__ == '__main__':
    '''
    The purpose of this code is to test if the functions above are operating as intended
    '''
    
    print('we will now test if the encoder and decoder works')
    d0 = ['l33t','1234']
    d1 = ['0984','asdw']
    d2 = ['kzje','2f4a']
    list_of_drives = [d0,d1,d2]
    drive_list = assign_drive_ids(drives_to_int(list_of_drives))
    print(f' the drives are {drive_list}')
    
    Q = Q_encoder(drive_list)
    P = P_encoder(drive_list)
    print(f' the backup Q drive is {Q}')
    
    print('\nnow imagine d0 is lost')
    remaining_drives = drive_list.copy()
    remaining_drives.pop(0)
    d0x = Q_decoder(Q, remaining_drives, 0)
    print(f' the original drive was \n {d0} \n and the recovered drive is \n {d0x[0]}')    
    
    print('\nnow imagine d1 is lost')
    remaining_drives = drive_list.copy()
    remaining_drives.pop(1)
    d1x = Q_decoder(Q, remaining_drives, 1)
    print(f' the original drive was \n {d1} \n and the recovered drive is \n {d1x[0]}')
    
    print('\nnow imagine d2 is lost')
    remaining_drives = drive_list.copy()
    remaining_drives.pop(2)
    d2x = Q_decoder(Q, remaining_drives, 2)
    print(f' the original drive was \n {d2} \n and the recovered drive is \n {d2x[0]}')
    
    print('\nNow imagine d1 and d2 are lost')
    remaining_drives = drive_list.copy()
    remaining_drives.pop(1)
    remaining_drives.pop(1)
    d1x, d2x = two_drives_lost(P,Q, remaining_drives, 1, 2)
    print(f' \nthe original drive was \n {convert_to_int(d1)} \n and the recovered drive is \n {d1x[0]}')
    print(f' \nthe original drive was \n {convert_to_int(d2)} \n and the recovered drive is \n {d2x[0]}')
    print(f' \nthe original drive in characters was \n {d1} \n and the recovered drive is \n {convert_to_chr(d1x[0])}')
    print(f' \nthe original drive in characters was \n {d2} \n and the recovered drive is \n {convert_to_chr(d2x[0])}')
    
