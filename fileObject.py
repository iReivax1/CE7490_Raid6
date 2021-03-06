import numpy as np
import string
import logging


#Each file is a simulator file to the file system in OS
class FileObject(object):

    def __init__(self):
        self.data = None
        
    def set_file_content(self, data):
        self.data = data
    
    def get_file_content(self):
        return np.array(self.data)
    

    #generate 'data_size' number of ascii characters
    def generate_random_data(self, data_size):
        ascii_list = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
        #no 0, 0 is used for padding
        # digits_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        #randomly selects # of characters from above
        self.data = np.random.choice(ascii_list, size=data_size)
        logging.info('Generating string {0}'.format(str(self.data)))
  