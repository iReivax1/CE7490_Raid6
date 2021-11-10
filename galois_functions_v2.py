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
    if bool(arr.ndim > 1): #recurssion if the list of drives is nested
        for i in list_of_drives:
            drives.append(drives_to_int(i))
            
    else: #only when the list of drives is no longer nested, i.e. it is only a single drive, convert the values in the drive to int
        print(list_of_drives)
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

def q_drive_encoder(drive, drive_ids):
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

def Q_encoder(disk_list):
    '''
    Parameters
    ----------
    disk_list: a list of diskObjects with .get_data_block() and .get_id() implemented
    
    Returns
    -------
    Q : The values for the Q drive in GF(2**8)

    '''
    Q = GF256(0)
    for i in disk_list:
        enc = q_drive_encoder(convert_to_int(i.get_data_block()), i.get_id())
        Q = Q + enc
        
    return Q 


def P_encoder(disk_list):
    '''
    Parameters
    ----------
    disk_list: a list of diskObjects with .get_data_block() and .get_id() implemented

    Returns
    -------
    P : The values for the P drive

    '''
    P = GF256(0)
    for i in disk_list:
        enc = drive_to_gf(convert_to_int(i.get_data_block()))
        P = P + enc
    return P
    

def Q_decoder(Q, remaining_disks, missing_disk_id):
    '''
    Parameters
    ----------
    This function is for the case where 1 drive fails
    
    Q : The values of the backup Q drive encoded as GF(2**8)
    remaining_drives : a list of diskObjects with .get_data_block() and .get_id() implemented
    missing_drive_id: This should be the drive id of the missing drive. It should be a single integer

    Returns
    -------
    The values of the missing drive

    '''
    GF = galois.GF(2**8)
    g = GF(2)
    cp255 = coprimes_of_255()
    i = cp255[missing_disk_id]
    
    Qx = Q_encoder(remaining_disks)
    D = (Q+Qx)/(g**i)
    return D
    
def P_decoder(P, remaining_disks, missing_disk_id):
    '''
    This function is for the case where 1 data drive fails
    
    Parameters
    ----------
    Q : The values of the backup Q drive
    remaining_drives : the values of the remaining drives
    remaining_drives : a list of diskObjects with .get_data_block() and .get_id() implemented
    missing_drive_id: This should be the drive id of the missing drive. It should be a single integer

    Returns
    -------
    The values of the missing drive

    '''

    Px = P_encoder(remaining_disks)
    D = P-Px
    return D

def two_drives_lost(P, Q, remaining_disks, missing_disk_id_1, missing_disk_id_2):
    '''
    The purpose of this function is to reconstruct the drives if two data drives go missing
    
    Parameters
    ----------
    P : The values stored in the P drive
    Q : The values stored in the  Q drive
    remaining_drives : a list of diskObjects with .get_data_block() and .get_id() implemented
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
    x = cp255[missing_disk_id_1]
    y = cp255[missing_disk_id_2]
    
    gyx = g**y/g**x
    
    A = (gyx)/(gyx+GF(1))
    B = (g**(-x))/(gyx+GF(1))

    Pxy = P_encoder(remaining_disks)
    Qxy = Q_encoder(remaining_disks)

    #reconstruction
    Dx = (A*(P+Pxy)) + (B*(Q+Qxy))
    Dy = (P+Pxy) + Dx
    
    return Dx, Dy
    
