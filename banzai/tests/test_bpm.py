import pytest
import mock
import numpy as np

from banzai.bpm import BadPixelMaskLoader
from banzai.tests.utils import FakeImage, FakeContext, FakeLCOObservationFrame, FakeCCDData


pytestmark = pytest.mark.bpm


@pytest.fixture(scope='module')
def set_random_seed():
    np.random.seed(81232385)


def make_test_bpm(nx, ny, bad_pixel_fraction=0.1, make_3d=False):
    if make_3d:
        n_total = 4 * nx * ny
        final_shape = (4, ny, nx)
    else:
        n_total = nx * ny
        final_shape = (ny, nx)
    bpm = np.zeros(n_total, dtype=int)
    bad_pixels = np.random.choice(range(nx*ny), int(bad_pixel_fraction*n_total))
    bpm[bad_pixels] = 1
    return bpm.reshape(final_shape)


def test_null_input_imags():
    tester = BadPixelMaskLoader(None)
    image = tester.run(None)
    assert image is None


@mock.patch('banzai.images.LCOFrameFactory.open')
@mock.patch('banzai.calibrations.CalibrationUser.get_calibration_filename', return_value='test.fits')
def test_adds_good_bpm(mock_bpm_name, mock_bpm, set_random_seed):
    image = FakeLCOObservationFrame(hdu_list=[FakeCCDData(memmap=False)])
    master_image = FakeLCOObservationFrame(hdu_list=[FakeCCDData(data=make_test_bpm(101,103), memmap=False)],
                                           file_path='test.fits')
    mock_bpm.return_value = master_image
    tester = BadPixelMaskLoader(FakeContext())
    image = tester.do_stage(image)
    np.testing.assert_array_equal(image.mask, master_image.data)
    assert image.meta.get('L1IDMASK') == 'test.fits'


@mock.patch('banzai.images.LCOFrameFactory.open')
@mock.patch('banzai.calibrations.CalibrationUser.get_calibration_filename', return_value='test.fits')
def test_adds_good_bpm_3d(mock_bpm_name, mock_bpm, set_random_seed):
    image = FakeLCOObservationFrame(hdu_list=[FakeCCDData(memmap=False) for i in range(4)])
    master_image = FakeLCOObservationFrame(hdu_list=[FakeCCDData(data=bpm_data, memmap=False) for bpm_data in make_test_bpm(101, 103, make_3d=True)],
                                           file_path='test.fits')

    mock_bpm.return_value = master_image
    tester = BadPixelMaskLoader(FakeContext())
    image = tester.do_stage(image)
    for image_hdu, master_hdu in zip(image.ccd_hdus, master_image.ccd_hdus):
        np.testing.assert_array_equal(image_hdu.mask, master_hdu.data)
    assert image.meta.get('L1IDMASK') == 'test.fits'


@mock.patch('banzai.calibrations.CalibrationUser.get_calibration_filename', return_value=None)
def test_removes_image_if_file_missing(mock_bpm_filename):
    image = FakeCCDData()
    tester = BadPixelMaskLoader(FakeContext(override_missing=False))
    assert tester.do_stage(image) is None


@mock.patch('banzai.calibrations.CalibrationUser.get_calibration_filename', return_value=None)
def test_uses_fallback_if_bpm_missing_and_no_bpm_set(mock_get_bpm_filename):
    image = FakeLCOObservationFrame(hdu_list=[FakeCCDData(memmap=False)])
    fallback_bpm = np.zeros(image.data.shape, dtype=np.uint8)
    tester = BadPixelMaskLoader(FakeContext(no_bpm=True, override_missing=True))
    assert tester.do_stage(image) is not None
    np.testing.assert_array_equal(image.bpm, fallback_bpm)
#
#
# @mock.patch('banzai.bpm.dbs.get_bpm_filename')
# @mock.patch('banzai.bpm.load_bpm')
# def test_removes_image_if_wrong_shape(mock_load_bpm, mock_get_bpm_filename, set_random_seed):
#     image = FakeImageForBPM()
#     mock_get_bpm_filename.return_value = 'fake_bpm_filename'
#     mock_load_bpm.return_value = make_test_bpm(image.nx+1, image.ny)
#     tester = BadPixelMaskLoader(FakeContextForBPM())
#     assert tester.do_stage(image) is None
#
#
# @mock.patch('banzai.bpm.dbs.get_bpm_filename')
# @mock.patch('banzai.bpm.load_bpm')
# def test_removes_image_wrong_shape_3d(mock_load_bpm, mock_get_bpm_filename, set_random_seed):
#     image = FakeImageForBPM(make_image_3d=True)
#     mock_get_bpm_filename.return_value = 'fake_bpm_filename'
#     mock_load_bpm.return_value = make_test_bpm(image.nx, image.ny)
#     tester = BadPixelMaskLoader(FakeContextForBPM())
#     assert tester.do_stage(image) is None
