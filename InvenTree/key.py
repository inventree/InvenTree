# Generate a SECRET_KEY file

import random
import string
import os

fn = 'secret_key.txt'

def generate_key():
	return ''.join(random.choices(string.digits + string.ascii_letters + string.punctuation, k=50))

if __name__ == '__main__':

    # Ensure key file is placed in same directory as this script
    path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(path, fn)

    with open(key_file, 'w') as key:
        key.write(generate_key())
        print('Generated SECRET_KEY to {f}'.format(f=key_file))