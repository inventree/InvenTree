# Generate a SECRET_KEY file

import random
import string
import os
import sys
import argparse

KEY_FN = 'secret_key.txt'
KEY_DIR = os.path.dirname(os.path.realpath(__file__))


def generate_key():
    options = string.digits + string.ascii_letters + string.punctuation
    key = ''.join([random.choice(options) for i in range(50)])
    return key


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Generate Django SECRET_KEY file')
    parser.add_argument('--output', help='Specify key file path', default=None)
    parser.add_argument('--force', '-f', help='Override key file (if it exists)', action='store_true')
    parser.add_argument('--dummy', '-d', help='Dummy run (display key only', action='store_true')
    
    args = parser.parse_args()

    if args.output:
        key_filename = args.output
    else:
        key_filename = os.path.join(KEY_DIR, KEY_FN)

    key_data = generate_key()

    if args.dummy:
        print('SECRET_KEY: {k}'.format(k=key_data))
        sys.exit(0)

    if not args.force and os.path.exists(key_filename):
        print("Key file already exists - '{f}'".format(f=key_filename))
        sys.exit(0)

    with open(key_filename, 'w') as key_file:
        print("Generating SECRET_KEY file - '{f}'".format(f=key_filename))
        key_file.write(key_data)
