"""Script to check a data file exported using the 'export-records' command."""

import argparse
import json
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check exported data file')
    parser.add_argument('datafile', help='Path to the exported data file (JSON)')

    args = parser.parse_args()

    if not os.path.isfile(args.datafile):
        print(f'Error: File not found: {args.datafile}')
        exit(1)

    with open(args.file, encoding='utf-8') as f:
        try:
            data = json.load(f)
            print(f'Successfully loaded data from {args.file}')
            print(f'Number of records: {len(data)}')
        except json.JSONDecodeError as e:
            print(f'Error: Failed to parse JSON file: {e}')
            exit(1)

    # TODO: Actually look at the data and check that it has the expected structure and content.
