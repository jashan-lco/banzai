import mock
import pytest

from datetime import datetime, timedelta
from unittest.mock import ANY

from celery.exceptions import Retry

from banzai.celery import stack_calibrations, schedule_calibration_stacking
from banzai.settings import CALIBRATION_STACK_DELAYS
from banzai.utils import date_utils
from banzai.context import Context
from banzai.tests.utils import FakeInstrument
from banzai.tests.bias_utils import FakeBiasImage

# TODO: update tests to use same mock lake data as e2e tests

fake_blocks_response_json = {
    "results": [
        {
            "end": "2019-02-19T21:55:09",
            "telescope": "2m0a",
            "request": {
                "configurations": [
                    {
                        "priority": 0,
                        "instrument_type": "2M0-SCICAM-SPECTRAL",
                        "instrument_configs": [
                            {
                                "exposure_time": 0.01,
                                "exposure_count": 2,
                                "rotator_mode": "",
                                "optical_elements": {},
                                "mode": "",
                                "extra_params": {},
                                "bin_y": 1,
                                "bin_x": 1
                            }
                        ],
                        "target": {
                            "type": "ICRS",
                            "name": "my target",
                            "extra_params": {}
                        },
                        "acquisition_config": {
                            "mode": "OFF",
                            "extra_params": {}
                        },
                        "extra_params": {},
                        "type": "BIAS",
                        "guiding_config": {
                            "optical_elements": {},
                            "exposure_time": 10,
                            "optional": True,
                            "mode": "ON",
                            "extra_params": {}
                        },
                        "constraints": {
                            "max_airmass": 20,
                            "extra_params": {},
                            "min_lunar_distance": 0
                        }
                    },
                    {
                        "priority": 1,
                        "instrument_type": "2M0-SCICAM-SPECTRAL",
                        "instrument_configs": [
                            {
                                "exposure_time": 0.01,
                                "exposure_count": 2,
                                "rotator_mode": "",
                                "optical_elements": {},
                                "mode": "",
                                "extra_params": {},
                                "bin_y": 1,
                                "bin_x": 1
                            }
                        ],
                        "target": {
                            "type": "ICRS",
                            "name": "my target",
                            "extra_params": {}
                        },
                        "acquisition_config": {
                            "mode": "OFF",
                            "extra_params": {}
                        },
                        "extra_params": {},
                        "type": "SKY_FLAT",
                        "guiding_config": {
                            "optical_elements": {},
                            "exposure_time": 10,
                            "optional": True,
                            "mode": "ON",
                            "extra_params": {}
                        },
                        "constraints": {
                            "max_airmass": 20,
                            "extra_params": {},
                            "min_lunar_distance": 0
                        }
                    }
                ]
            },
            "site": "coj",
            "start": "2019-02-19T20:27:49",
            "state": "PENDING",
            "proposal": "calibrate",
            "enclosure": "clma",
            "name": ""
        },
        {
            "end": "2019-02-20T09:55:09",
            "telescope": "2m0a",
            "request": {
                "configurations": [
                    {
                        "priority": 0,
                        "instrument_type": "2M0-SCICAM-SPECTRAL",
                        "instrument_configs": [
                            {
                                "exposure_time": 0.01,
                                "exposure_count": 2,
                                "rotator_mode": "",
                                "optical_elements": {},
                                "mode": "",
                                "extra_params": {},
                                "bin_y": 1,
                                "bin_x": 1
                            }
                        ],
                        "target": {
                            "type": "ICRS",
                            "name": "my target",
                            "extra_params": {}
                        },
                        "acquisition_config": {
                            "mode": "OFF",
                            "extra_params": {}
                        },
                        "extra_params": {},
                        "type": "BIAS",
                        "guiding_config": {
                            "optical_elements": {},
                            "exposure_time": 10,
                            "optional": True,
                            "mode": "ON",
                            "extra_params": {}
                        },
                        "constraints": {
                            "max_airmass": 20,
                            "extra_params": {},
                            "min_lunar_distance": 0
                        }
                    }
                ]
            },
            "site": "coj",
            "start": "2019-02-20T08:27:49",
            "state": "PENDING",
            "proposal": "calibrate",
            "enclosure": "clma",
            "name": ""
        }
    ],
}

fake_instruments_response = FakeInstrument()


class TestMain():
    @pytest.fixture(scope='function')
    def setup(self):
        self.site = 'coj'
        self.min_date = '2019-02-19T20:27:49'
        self.max_date = '2019-02-20T09:55:09'
        self.context = Context({'db_address': 'db_address', 'CALIBRATION_IMAGE_TYPES': ['BIAS'],
                                'CALIBRATION_STACK_DELAYS': {'BIAS': 300}})
        self.frame_type = 'BIAS'
        self.fake_blocks_response_json = fake_blocks_response_json
        self.fake_inst = FakeInstrument(site='coj', camera='2m0-SciCam-Spectral', enclosure='clma', telescope='2m0a')

    @mock.patch('banzai.celery.stack_calibrations.apply_async')
    @mock.patch('banzai.celery.dbs.get_instruments_at_site')
    @mock.patch('banzai.utils.observation_utils.get_calibration_blocks_for_time_range')
    @mock.patch('banzai.utils.observation_utils.filter_calibration_blocks_for_type')
    def test_submit_stacking_tasks_to_queue_no_delay(self, mock_filter_blocks, mock_get_blocks, mock_get_instruments,
                                                     mock_stack_calibrations, setup):
        mock_get_instruments.return_value = [self.fake_inst]
        mock_get_blocks.return_value = self.fake_blocks_response_json
        mock_filter_blocks.return_value = [block for block in self.fake_blocks_response_json['results']]
        schedule_calibration_stacking(self.site, self.context, self.min_date, self.max_date)
        mock_stack_calibrations.assert_called_with(args=(self.min_date, self.max_date, self.fake_inst.id,
                                                         self.frame_type, vars(self.context),
                                                         mock_filter_blocks.return_value),
                                                   countdown=0)

    @mock.patch('banzai.celery.stack_calibrations.apply_async')
    @mock.patch('banzai.celery.dbs.get_instruments_at_site')
    @mock.patch('banzai.utils.observation_utils.get_calibration_blocks_for_time_range')
    @mock.patch('banzai.utils.observation_utils.filter_calibration_blocks_for_type')
    def test_submit_stacking_tasks_to_queue_with_delay(self, mock_filter_blocks, mock_get_blocks, mock_get_instruments,
                                                       mock_stack_calibrations, setup):
        mock_get_instruments.return_value = [self.fake_inst]
        self.fake_blocks_response_json['results'][0]['end'] = datetime.strftime(datetime.utcnow() + timedelta(minutes=1),
                                                                                date_utils.TIMESTAMP_FORMAT)
        mock_get_blocks.return_value = self.fake_blocks_response_json
        mock_filter_blocks.return_value = [block for block in self.fake_blocks_response_json['results']]
        schedule_calibration_stacking(self.site, self.context, self.min_date, self.max_date)
        mock_stack_calibrations.assert_called_with(args=(self.min_date, self.max_date, self.fake_inst.id,
                                                         self.frame_type, vars(self.context),
                                                         mock_filter_blocks.return_value),
                                                   countdown=(60+CALIBRATION_STACK_DELAYS['BIAS']))

    @mock.patch('banzai.calibrations.process_master_maker')
    @mock.patch('banzai.celery.dbs.get_individual_calibration_image_records')
    @mock.patch('banzai.celery.dbs.get_instrument_by_id')
    def test_stack_calibrations(self, mock_get_instrument, mock_get_calibration_images, mock_process_master_maker, setup):
        mock_get_instrument.return_value = self.fake_inst
        mock_get_calibration_images.return_value = [FakeBiasImage(), FakeBiasImage()]
        stack_calibrations(self.min_date, self.max_date, 1, self.frame_type, self.context,
                           [self.fake_blocks_response_json['results'][0]])
        mock_process_master_maker.assert_called_with(self.fake_inst, self.frame_type, self.min_date, self.max_date, ANY)

    @mock.patch('banzai.calibrations.process_master_maker')
    @mock.patch('banzai.celery.dbs.get_individual_calibration_image_records')
    @mock.patch('banzai.celery.dbs.get_instrument_by_id')
    def test_stack_calibrations_not_enough_images(self, mock_get_instrument, mock_get_calibration_images, mock_process_master_maker, setup):
        mock_get_instrument.return_value = self.fake_inst
        mock_get_calibration_images.return_value = [FakeBiasImage()]
        with pytest.raises(Retry) as e:
            stack_calibrations(self.min_date, self.max_date, 1, self.frame_type, self.context,
                               [self.fake_blocks_response_json['results'][0]])
        assert e.type is Retry
