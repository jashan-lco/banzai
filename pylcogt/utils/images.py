from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy import units
from pylcogt.utils import date_utils
from pylcogt.utils.fits_utils import table_to_fits
from pylcogt import dbs
import numpy as np

class Image(object):
    def __init__(self, filename):

        hdu = fits.open(filename, 'readonly')
        self.data = hdu[0].data.astype(np.float)
        self.header = hdu[0].header
        self.site = hdu[0].header['SITEID']
        self.instrument = hdu[0].header['INSTRUME']
        self.epoch = hdu[0].header['DAY-OBS']
        self.nx = hdu[0].header['NAXIS1']
        self.ny = hdu[0].header['NAXIS2']
        self.filename = filename
        self.ccdsum = hdu[0].header['CCDSUM']
        self.filter = hdu[0].header['FILTER']
        self.telescope_id = dbs.get_telescope_id(self.site, self.instrument)
        self.obstype = hdu[0].header['OBSTYPE']
        self.exptime = float(hdu[0].header['EXPTIME'])
        self.dateobs = date_utils.parse_date_obs(hdu[0].header['DATE-OBS'])
        self.readnoise = float(hdu[0].header['RDNOISE'])
        self.catalog = None
        coord = SkyCoord(hdu[0].header['RA'], hdu[0].header['DEC'], unit=(units.hourangle, units.degree))
        self.ra = coord.ra.deg
        self.dec = coord.dec.deg
        self.pixel_scale = float(hdu[0].header['PIXSCALE'])

    def subtract(self, value):
        return self.data - value

    def writeto(self, filename):
        table_hdu = table_to_fits(self.catalog)
        image_hdu = fits.PrimaryHDU(self.data, header=self.header)
        image_hdu.header['EXTEND'] = True
        hdu_list = fits.HDUList([image_hdu, table_hdu])
        hdu_list.writeto(filename, clobber=True)

    def update_shape(self, nx, ny):
        self.nx = nx
        self.ny = ny

    def write_catalog(self, filename, nsources=None):
        self.catalog[:nsources].write(filename, format='fits', overwrite=True)