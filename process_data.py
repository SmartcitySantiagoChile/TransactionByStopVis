import argparse
import csv
import gzip
import os
import sys
from collections import defaultdict

from decouple import config
from pyfiglet import Figlet

from aws import AWSSession

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(DIR_PATH, 'data')
INPUTS_PATH = os.path.join(DIR_PATH, 'inputs')
TEMPLATE_PATH = os.path.join(DIR_PATH, 'template')
OUTPUTS_PATH = os.path.join(DIR_PATH, 'outputs')


def main(argv):
    """
    This script will create visualization of bip! transaction by stop for each day.
    """
    f = Figlet()
    print(f.renderText('Welcome DTPM'))

    # Arguments and description
    parser = argparse.ArgumentParser(description='create visualization of bip! transaction by stop for each day.')

    parser.add_argument('start_date', help='Lower bound time. For instance 2020-01-01')
    parser.add_argument('end_date', help='Upper bound time. For instance 2020-12-31')
    parser.add_argument('output_filename', help='filename of html file created by the process')

    args = parser.parse_args(argv[1:])

    start_date = args.start_date
    end_date = args.end_date
    output_filename = args.output_filename

    aws_session = AWSSession()
    MAPBOX_KEY = config('MAPBOX_KEY')

    available_dates = aws_session.get_available_dates()

    dates_in_range = []
    for date in available_dates:
        if date < start_date:
            continue
        if date > end_date:
            break
        dates_in_range.append(date)

    if not dates_in_range:
        print('There is not data between {0} and {1}'.format(start_date, end_date))
        exit(1)

    print('dates found in period: {0}'.format(len(dates_in_range)))

    available_files = []
    for date in dates_in_range:
        filename = '{0}.transaction.gz'.format(date.strftime('%Y-%m-%d'))
        file_path = os.path.join(DATA_PATH, filename)
        if os.path.exists(file_path):
            print('file {0} exists in local storage ... skip'.format(filename))
            available_files.append(file_path)
        else:
            aws_session.download_object_from_bucket(filename, DATA_PATH)

    output = defaultdict(lambda: dict(info=dict, dates=defaultdict(lambda: 0)))
    for file_path in available_files:
        print('reading file "" ...'.format(os.path.basename(file_path)))
        with gzip.open(file_path, mode='r', encoding='utf-8') as file_obj:
            for line in file_obj.readlines():
                values = line.split(';')
                stop_code = values[3]
                stop_name = values[5]
                area = values[4]
                date = values[0]
                transactions = values[8]

                output[stop_code]['info']['name'] = stop_name
                output[stop_code]['info']['area'] = area
                output[stop_code]['dates'][date] += transactions

    # add location to stop data
    with open(os.path.join(INPUTS_PATH, 'stop.csv'), encoding='utf-8') as csv_file_obj:
        spamreader = csv.reader(csv_file_obj, delimiter=';')
        for row in spamreader:
            stop_code = row[0]
            stop_longitude = row[1]
            stop_latitude = row[2]

            output[stop_code]['info']['longitude'] = stop_longitude
            output[stop_code]['info']['latitude'] = stop_latitude

    # TODO: write data to kepler file

    # TODO: write mapbox_id to kepler file


if __name__ == "__main__":
    sys.exit(main(sys.argv))
