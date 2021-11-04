import numpy as np
import string
import logging


#Each file is a simulator file to the file system in OS
class File(object):

    def __init__(self):
        self.data = None
        
    def set_file_content(self, data):
        self.data = data
    
    def get_file_content(self):
        return np.array(self.data).tostring()

    def byte_to_string(bytes):
        try:
            string_data = str(bytes.decode('utf-8'))
            return string_data
        except Exception:
            print('not decodable')

    #generate 'data_size' number of ascii characters
    def generate_random_data(self, data_size):
        ascii_list = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
        #randomly selects # of characters from above
        self.data = np.random.choice(ascii_list, size=data_size)
        logging.info('Generating string {0}'.format(str(self.data.decode('utf-8'))))
  

    def update(self, idx, new_data):
        if idx > len(self.data):
            print ('index out of bound')
            return 
        else:
            self.data[idx] = new_data
            logging.info('File updated to {0} state'. format(datum for datum in self.data))
