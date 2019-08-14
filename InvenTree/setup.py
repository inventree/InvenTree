"""
Performs initial setup functions.

- Generates a Django SECRET_KEY file to be used by manage.py
- Copies config template file (if a config file does not already exist)
"""

import random
import string
import os
import sys
import argparse
from shutil import copyfile

OUTPUT_DIR = os.path.dirname(os.path.realpath(__file__))

KEY_FN = 'secret_key.txt'
CONFIG_FN = 'config.yaml'
CONFIG_TEMPLATE_FN = 'config_template.yaml'


def generate_key(length=50):
    """ Generate a random string

    Args:
        length: Number of characters in returned string (default = 50)

    Returns:
        Randomized secret key string
    """

    options = string.digits + string.ascii_letters + string.punctuation
    key = ''.join([random.choice(options) for i in range(length)])
    return key


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Generate Django SECRET_KEY file')
    parser.add_argument('--force', '-f', help='Override existing files', action='store_true')
    parser.add_argument('--dummy', '-d', help='Dummy run (do not create any files)', action='store_true')
    
    args = parser.parse_args()

    # Places to store files
    key_filename = os.path.join(OUTPUT_DIR, KEY_FN)
    conf_template = os.path.join(OUTPUT_DIR, CONFIG_TEMPLATE_FN)
    conf_filename = os.path.join(OUTPUT_DIR, CONFIG_FN)
    
    # Generate secret key data
    key_data = generate_key()

    if args.dummy:
        print('SECRET_KEY: {k}'.format(k=key_data))
        sys.exit(0)

    if not args.force and os.path.exists(key_filename):
        print("Key file already exists - '{f}'".format(f=key_filename))
    else:
        with open(key_filename, 'w') as key_file:
            print("Generating SECRET_KEY file - '{f}'".format(f=key_filename))
            key_file.write(key_data)

    if not args.force and os.path.exists(conf_filename):
        print("Config file already exists (skipping)")
    else:
        print("Copying config template to 'config.yaml'")
        copyfile(conf_template, conf_filename)
