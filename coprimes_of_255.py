# -*- coding: utf-8 -*-
"""
Created on Fri Nov  5 11:09:08 2021

@author: yipji
"""


import numpy as np

import galois

from math import gcd

def coprime(a, b):
    return gcd(a, b) == 1

def coprimes_of_255():
    coprimes_of_255 = []
    for i in range(1,255):
        if coprime(i,255):
            coprimes_of_255.append(i)
            # print(i)
    # coprimes_of_255.pop(0)
    return coprimes_of_255


if __name__ == '__main__':
    '''
    This portion of the code is used to 
    '''
    def test_generator(base=2):
        ### Setting up the parameters of the test ###
        GF256 = galois.GF(2**8) #definition of the galois field
        g = GF256(base) #the galois field generator. 
        lx = 0 #used to test if some repeat has occured
        l = [] #store output values for checking if repeat has occured
        error_messages = []
        cp255 = coprimes_of_255() #getting the coprimes of 255 as per our defined function
        
        ### Running the test ###
        for i in cp255:
            gx = g**i #generator output based on GF(2) to the power of coprimes of 255
            
            lx += sum(gx==l)
            
            if sum(gx==l)>0:
                # print(f"repeat found at {i} generator outputs {gx}")
                error_messages.append(f"repeat found at {i} generator outputs {gx}")            
                
            l.append(gx)
        if lx > 0:
            print(f"Some repeat has occured for base {base}")
            return [l, error_messages]
        else:
            print(f"no repeats for base {base}")
            return [l, error_messages]
    
    test1 = test_generator()
    '''
    To satisfy ourselves that this test works, 
    we can change the base to a different number 
    and the test should warn us about numerous repeats
    and return the message "Some repeat has occured" at the end
    
    Uncomment the line below to run the generator with base 3
    '''
    test2 = test_generator(3)
