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
    file = []
    for i in string:
        file.append(ord(i))
    return file

def convert_to_chr(array):
    file = ""
    for i in array:
        file += chr(i)
    return file

def convert_to_numpy(galois):
    file = []
    for i in galois:
        file.append(int(i))
    return file

def assign_drive_numbers(list_of_drives):
    drive_number = 0
    drive_list = []
    for i in list_of_drives:
        drive_list.append([i,drive_number])
        drive_number += 1
    return drive_list

def drive_to_gf(drive):
    '''
    this function expects a list of non-negative integers of arbitary length, where each integer <=255
    '''
    GF = galois.GF(2**8)
    return GF(drive)

def drive_encoder(drive, drive_number):
    '''
    file: a list of non-negative integers of arbitary length, where each integer <=255
    drive_number: the unique number associated with the drive in the range of [0,255]
    returns: the GF encoding for the drive, multiple GF encodings will be summed to form the Q backup drive
    '''
    GF = galois.GF(2**8)
    g = GF(2)
    cp255 = coprimes_of_255()
    i = cp255[drive_number]
    m = drive_to_gf(drive)
    q = (g**i)*m
    return q

def Q_encoder(drive_list):
    '''
    Parameters
    ----------
    drive_list : The value of the list of drives to be backed up. 
    **NOTE** - The drive_list should be in the format [drive, drive_number]
    where drive is a list of integers; and
    drive_number is a single integer

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
    **NOTE** - The drive_list should be in the format [drive, drive_number]
    where drive is a list of integers; and
    drive_number is a single integer

    Returns
    -------
    P : The values for the P drive

    '''
    
    P = GF256(0)
    
    for drive, _ in drive_list:

        enc = drive_to_gf(drive)

        P = P+enc
        
    return P


def Q_decoder(Q, remaining_drives, missing_drive_number):
    '''
    Parameters
    ----------
    This function is for the case where 1 drive fails
    
    Q : The values of the backup Q drive encoded as GF(2**8)
    remaining_drives : the values of the remaining drives
    **NOTE** - The drive_list should be in the format [drive, drive_number]
    where drive is a list of integers; and
    drive_number is a single integer
    missing_drive_number: This should be the drive number of the missing drive. It should be a single integer

    Returns
    -------
    The values of the missing drive

    '''
    GF = galois.GF(2**8)
    g = GF(2)
    cp255 = coprimes_of_255()
    i = cp255[missing_drive_number]
    
    Qx = Q_encoder(remaining_drives)
    D = (Q+Qx)/(g**i)
    return convert_to_numpy(D)
    
def P_decoder(P, remaining_drives):
    '''
    Parameters
    ----------
    This function is for the case where 1 drive fails
    
    Q : The values of the backup Q drive encoded as GF(2**8)
    remaining_drives : the values of the remaining drives
    **NOTE** - The drive_list should be in the format [drive, drive_number]
    where drive is a list of integers; and
    drive_number is a single integer
    missing_drive_number: This should be the drive number of the missing drive. It should be a single integer

    Returns
    -------
    The values of the missing drive

    '''
    GF = galois.GF(2**8)
    
    Px = P_encoder(remaining_drives)
    D = P-Px
    return convert_to_numpy(D)

def two_drives_lost(P, Q, remaining_drives, missing_drive_number_1, missing_drive_number_2):
    
    
    #setting up the Galois parameters
    GF = galois.GF(2**8)
    g = GF(2)
    cp255 = coprimes_of_255()
    
    #precomputed constants
    x = cp255[missing_drive_number_1]
    y = cp255[missing_drive_number_2]
    
    gyx = g**y/g**x
    
    A = (gyx)*((gyx+GF(1))**-1)
    print(A)
    B = (g**(-x))/(gyx+GF(1))
    print(B)
    
    Pxy = P_encoder(remaining_drives)
    print(Pxy)
    Qxy = Q_encoder(remaining_drives)
    print(Qxy)
    
    Dx = (A*(P+Pxy)) + (B*(Q+Qxy))
    Dy = (P+Pxy) + Dx
    
    return convert_to_numpy(Dx), convert_to_numpy(Dy)

if __name__ == '__main__':
    print('we will now test if the encoder and decoder works')
    d0 = convert_to_int('l33t')
    d1 = convert_to_int('0984')
    d2 = convert_to_int('kzje')
    drive_list = assign_drive_numbers([d0,d1,d2])
    print(f' the drives are {drive_list}')
    Q = Q_encoder(drive_list)
    P = P_encoder(drive_list)
    print(f' the backup Q drive is {Q}')
    
    # print('\nnow imagine d0 is lost')
    # remaining_drives = drive_list.copy()
    # remaining_drives.pop(0)
    # d0x = Q_decoder(Q, remaining_drives, 0)
    # print(f' the original drive was \n {d0} \n and the recovered drive is \n {d0x}')    
    
    # print('\nnow imagine d1 is lost')
    # remaining_drives = drive_list.copy()
    # remaining_drives.pop(1)
    # d1x = Q_decoder(Q, remaining_drives, 1)
    # print(f' the original drive was \n {d1} \n and the recovered drive is \n {d1x}')
    
    # print('\nnow imagine d2 is lost')
    # remaining_drives = drive_list.copy()
    # remaining_drives.pop(2)
    # d2x = Q_decoder(Q, remaining_drives, 2)
    # print(f' the original drive was \n {d2} \n and the recovered drive is \n {d2x}')
    
    print('\nNow imagine d1 and d2 are lost')
    remaining_drives = drive_list.copy()
    remaining_drives.pop(1)
    remaining_drives.pop(1)
    d1x, d2x = two_drives_lost(P,Q, remaining_drives, 1, 2)
    print(f' \nthe original drive was \n {d1} \n and the recovered drive is \n {d1x}')
    print(f' \nthe original drive was \n {d2} \n and the recovered drive is \n {d2x}')
    
