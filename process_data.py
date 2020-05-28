# -*- coding: utf8 -*-
import argparse
import csv
import gzip
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

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

    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
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
            aws_session.download_object_from_bucket(filename, file_path)

    output = defaultdict(lambda: dict(info=dict(), dates=defaultdict(lambda: 0)))
    for file_path in available_files:
        print('reading file "" ...'.format(os.path.basename(file_path)))
        with gzip.open(file_path, str('rt'), encoding='latin-1') as file_obj:
            file_obj.readline()
            for line in file_obj.readlines():
                values = line.split(';')
                stop_code = values[0].encode('latin-1').decode('utf-8')

                if stop_code == "-":
                    pass
                stop_name = values[7]
                area = values[6]
                date = values[3]
                transactions = values[8]

                output[stop_code]['info']['name'] = stop_name
                output[stop_code]['info']['area'] = area
                output[stop_code]['dates'][date] += int(transactions)

    # add location to stop data
    with open(os.path.join(INPUTS_PATH, 'stop.csv'), encoding='latin-1') as csv_file_obj:
        spamreader = csv.reader(csv_file_obj, delimiter=',')
        next(spamreader)
        for row in spamreader:
            stop_code = row[5]
            stop_longitude = row[7]
            stop_latitude = row[8]

            output[stop_code]['info']['longitude'] = float(stop_longitude)
            output[stop_code]['info']['latitude'] = float(stop_latitude)

    # add location to metro station data
    with open(os.path.join(DATA_PATH, 'metro.geojson')) as metro:
        data = json.load(metro)
        for i in data['features']:
            metro_station = i['properties']['name']

    # save csv data
    with open(os.path.join(OUTPUTS_PATH, output_filename + '.csv'), 'w', encoding='latin-1') as outfile:
        data_csv = []
        w = csv.writer(outfile)
        w.writerow(['fecha', 'nombre', 'comuna', 'latitud', 'longitud', 'subidas'])
        for data in dict(output):
            info = dict(output)[data]['info']
            longitude = '-'
            latitude = '-'
            area = '-'
            valid = True
            if 'longitude' in dict(output)[data]['info']:
                longitude = info['longitude']
            else:
                print("Warning: %s doesn't have longitude" % data)
                valid = False

            if 'latitude' in dict(output)[data]['info']:
                latitude = info['latitude']
            else:
                print("Warning: %s doesn't have latitude" % data)
                valid = False

            if 'area' in dict(output)[data]['info']:
                area = info['area']
            else:
                print("Warning: %s doesn't have area" % data)
                valid = False

            name = data
            for date in dict(output)[data]['dates']:
                if valid:
                    data_row = [date + " 00:00:00", name, area, longitude, latitude, dict(output)[data]['dates'][date]]
                    w.writerow(data_row)
                    data_csv.append(data_row)

    # write mapbox_id to kepler file
    html_file = open(os.path.join(TEMPLATE_PATH, 'template.html'))
    html_data = html_file.read()
    html_file.close()
    with open(os.path.join(OUTPUTS_PATH, f"{output_filename}.html"), 'w') as output:
        new_html_data = html_data.replace("<MAPBOX_KEY>", MAPBOX_KEY).replace("<DATA>", str(data_csv))
        output.write(new_html_data)


if __name__ == "__main__":
    sys.exit(main(sys.argv))