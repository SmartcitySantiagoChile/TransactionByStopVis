import filecmp
import os
from collections import defaultdict
from datetime import datetime
from unittest import TestCase

import mock
import logging
import process_data


class ProcessDataTest(TestCase):

    def setUp(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.data_path = os.path.join(dir_path, 'files')
        self.test_html_path = os.path.join(self.data_path, '2020-05-09.4daytransactionbystop.html')
        self.test_csv_path = os.path.join(self.data_path, '2020-05-09.4daytransactionbystop.csv')
        logging.disable(logging.CRITICAL)


    @mock.patch('process_data.AWSSession')
    def test_check_available_days(self, aws_session):
        aws_session.get_available_dates.return_value = [datetime.strptime('2019-02-05', "%Y-%m-%d"),
                                                        datetime.strptime('2020-02-05', "%Y-%m-%d"),
                                                        datetime.strptime('2021-02-05', "%Y-%m-%d")]
        start_date = datetime.strptime('2020-01-01', "%Y-%m-%d")
        end_date = datetime.strptime('2020-12-31', "%Y-%m-%d")
        available_days = process_data.check_available_days(aws_session, start_date, end_date)
        self.assertEqual(datetime.strptime('2020-02-05', "%Y-%m-%d"), available_days[0])

    @mock.patch('process_data.AWSSession')
    def test_get_available_files_exist(self, aw_session):
        dates_in_range = [datetime.strptime('2020-05-08', "%Y-%m-%d")]
        correct_path = [os.path.join(self.data_path, '2020-05-08.4daytransactionbystop.gz')]
        self.assertEqual(correct_path, process_data.get_available_files(dates_in_range, aw_session, self.data_path))

    @mock.patch('process_data.AWSSession')
    def test_get_availble_files_doesnt_exist(self, aw_session):
        dates_in_range = [datetime.strptime('2020-06-08', "%Y-%m-%d")]
        correct_path = [os.path.join(self.data_path, '2020-06-08.4daytransactionbystop.gz')]
        aw_session.download_object_from_bucket.return_value = correct_path[0]
        self.assertEqual(correct_path, process_data.get_available_files(dates_in_range, aw_session, self.data_path))

    def test_get_output_dict(self):
        available_files = [os.path.join(self.data_path, '2020-05-09.4daytransactionbystop.gz')]
        expected_output = defaultdict(lambda: dict(info=dict(), dates=defaultdict(lambda: 0)))
        expected_output['T-17-140-OP-80']['info']['auth_stop_code'] = 'T-17-140-OP-80'
        expected_output['T-17-140-OP-80']['info']['user_stop_code'] = 'PC1106'
        expected_output['T-17-140-OP-80']['info']['stop_name'] = 'Parada / Municipalidad de Las Condes'
        expected_output['T-17-140-OP-80']['info']['area'] = 'Las Condes'
        expected_output['T-17-140-OP-80']['dates']['2020-05-09'] = 3
        self.assertDictEqual(expected_output['T-17-140-OP-80'],
                             process_data.get_output_dict(available_files)[0]['T-17-140-OP-80'])

    def test_add_location_to_stop_data(self):
        dates_in_range = [datetime.strptime('2020-05-09', "%Y-%m-%d")]
        expected_output = defaultdict(lambda: dict(info=dict(), dates=defaultdict(lambda: 0)))
        expected_output['T-17-140-OP-80']['info']['auth_stop_code'] = 'T-17-140-OP-80'
        expected_output['T-17-140-OP-80']['info']['area'] = 'LAS CONDES'
        expected_output['T-17-140-OP-80']['dates']['2020-05-08'] = 3
        output = process_data.add_location_to_stop_data(self.data_path, expected_output, dates_in_range)
        expected_output['T-17-140-OP-80']['info']['longitude'] = -33.41611369
        expected_output['T-17-140-OP-80']['info']['latitude'] = -70.59369329
        self.assertDictEqual(output, expected_output)

    def test_add_location_to_metro_station_data(self):
        dates_in_range = [datetime.strptime('2020-05-30', "%Y-%m-%d")]
        expected_output = defaultdict(lambda: dict(info=dict(), dates=defaultdict(lambda: 0)))
        expected_output['TOBALABAL4']['info']['auth_stop_code'] = 'Estación Tobalaba'
        expected_output['TOBALABAL4']['info']['area'] = 'Estación Tobalaba L4'
        expected_output['TOBALABAL4']['dates']['2020-05-30'] = 0
        output = process_data.add_location_to_metro_station_data(self.data_path, expected_output, ('TOBALABAL4'),
                                                                 dates_in_range)
        expected_output['TOBALABAL4']['info']['longitude'] = -33.418227
        expected_output['TOBALABAL4']['info']['latitude'] = -70.60145
        self.assertDictEqual(output, expected_output)

    def test_add_location_to_metrotren_station_data(self):
        dates_in_range = [datetime.strptime('2020-05-30', "%Y-%m-%d")]
        expected_output = defaultdict(lambda: dict(info=dict(), dates=defaultdict(lambda: 0)))
        expected_output['Estacion Nos']['info']['auth_stop_code'] = 'Estacion Nos'
        expected_output['Estacion Nos']['info']['area'] = 'Estacion Nos'
        expected_output['Estacion Nos']['dates']['2020-05-30'] = 0
        output = process_data.add_location_to_metrotren_station_data(self.data_path, expected_output,
                                                                     dates_in_range)
        expected_output['Estacion Nos']['info']['longitude'] = -33.477086
        expected_output['Estacion Nos']['info']['latitude'] = -70.680622
        self.assertDictEqual(output, expected_output)

    def test_create_csv_data(self):
        output_filename = '2020-05-09.4daytransactionbystop'
        expected_output = defaultdict(lambda: dict(info=dict(), dates=defaultdict(lambda: 0)))
        expected_output['T-17-140-OP-80']['info']['auth_stop_code'] = 'T-17-140-OP-80'
        expected_output['T-17-140-OP-80']['info']['user_stop_code'] = 'PC1106'
        expected_output['T-17-140-OP-80']['info']['stop_name'] = 'Parada / Municipalidad de Las Condes'
        expected_output['T-17-140-OP-80']['info']['area'] = 'Las Condes'
        expected_output['T-17-140-OP-80']['dates']['2020-05-08'] = 3
        expected_output['T-17-140-OP-80']['info']['longitude'] = -33.41611369
        expected_output['T-17-140-OP-80']['info']['latitude'] = -70.59369329
        expected_output['ERROR']['info']['stop'] = 'Prueba con erroresss'
        expected_csv = [
            ['2020-05-08 00:00:00', 'Parada / Municipalidad de Las Condes', 'PC1106', 'T-17-140-OP-80', 'Las Condes',
             -33.41611369, -70.59369329, 3]]
        self.assertEqual(expected_csv, process_data.create_csv_data(self.data_path, output_filename, expected_output))

    def test_write_info_to_kepler_file(self):
        csv_data = [['2020-05-08 00:00:00', 'PC1106', 'LAS CONDES', -33.41611369, -70.59369329, 3]]
        output_filename = '2020-05-09.4daytransactionbystop'
        mapbox_key = "mapbox_key"
        process_data.write_info_to_kepler_file(self.data_path, self.data_path, output_filename, mapbox_key, csv_data)
        self.assertTrue(filecmp.cmp(os.path.join(self.data_path, '2020-05-09.4daytransactionbystop.html'),
                                    os.path.join(self.data_path, 'test_base.html')))

    @mock.patch('process_data.config')
    @mock.patch('process_data.write_info_to_kepler_file')
    @mock.patch('process_data.create_csv_data')
    @mock.patch('process_data.add_location_to_metrotren_station_data')
    @mock.patch('process_data.add_location_to_metro_station_data')
    @mock.patch('process_data.add_location_to_stop_data')
    @mock.patch('process_data.get_output_dict')
    @mock.patch('process_data.get_available_files')
    @mock.patch('process_data.check_available_days')
    @mock.patch('process_data.AWSSession')
    @mock.patch('process_data.OUTPUTS_PATH')
    @mock.patch('process_data.TEMPLATE_PATH')
    @mock.patch('process_data.INPUTS_PATH')
    @mock.patch('process_data.DATA_PATH')
    @mock.patch('process_data.DIR_PATH')
    def test_main(self, dir_path, data_path, input_path, template_path, output_path, aws_session, check_available_days,
                  get_available_files, output_dict, add_location_to_stop_data, add_location_to_metro_data,
                  add_location_to_metrotren_station_data, create_csv_data,
                  write_info_to_kepler_file, config):
        dir_path.return_value = self.data_path
        data_path.return_value = self.data_path
        input_path.return_value = self.data_path
        template_path.return_value = self.data_path
        output_path.return_value = self.data_path
        check_available_days.return_value = [datetime.strptime('2020-02-05', "%Y-%m-%d")]
        output_dict.return_value = [mock.MagicMock(), mock.MagicMock(), mock.MagicMock()]
        process_data.main(['process_data', '2020-05-08', '2020-05-08', 'output'])

    @mock.patch('process_data.config')
    @mock.patch('process_data.write_info_to_kepler_file')
    @mock.patch('process_data.create_csv_data')
    @mock.patch('process_data.add_location_to_stop_data')
    @mock.patch('process_data.get_output_dict')
    @mock.patch('process_data.get_available_files')
    @mock.patch('process_data.check_available_days')
    @mock.patch('process_data.AWSSession')
    @mock.patch('process_data.OUTPUTS_PATH')
    @mock.patch('process_data.TEMPLATE_PATH')
    @mock.patch('process_data.INPUTS_PATH')
    @mock.patch('process_data.DATA_PATH')
    @mock.patch('process_data.DIR_PATH')
    def test_main_without_days(self, dir_path, data_path, input_path, template_path, output_path, aws_session,
                               check_available_days,
                               get_available_files, output_dict, add_location_to_stop_data, create_csv_data,
                               write_info_to_kepler_file, config):
        dir_path.return_value = self.data_path
        data_path.return_value = self.data_path
        input_path.return_value = self.data_path
        template_path.return_value = self.data_path
        output_path.return_value = self.data_path
        check_available_days.return_value = []

        with self.assertRaises(SystemExit) as cm:
            process_data.main(['process_data', '2020-05-08', '2020-05-08', 'output'])

            self.assertEqual(cm.exception.code, 1)

    def tearDown(self):
        if os.path.exists(self.test_csv_path):
            os.remove(self.test_csv_path)
        if os.path.exists(self.test_html_path):
            os.remove(self.test_html_path)
