from pytel_andor.libandor import *
import logging
import matplotlib.pyplot as plt
import time
from astropy.io import fits

logging.basicConfig(format='[%(asctime)s] %(message)s', level=logging.DEBUG)

try:
    logging.info('init')
    init('/usr/local/etc/andor')
    logging.info('done')

    logging.info('Set Read Mode to --Image--')
    setReadMode(4)

    logging.info('Set Acquisition mode to --Single scan--')
    setAcquisitionMode(1)

    logging.info('Set initial exposure time')
    setExposureTime(1.)

    logging.info('Get Detector dimensions')
    width, height = getDetector();
    logging.info('Got %dx%d' % (width, height))
        
    logging.info('Initialize Shutter')
    setShutter(1, 0, 50, 50)
            
    logging.info('Setup Image dimensions')
    #width = height = 2000
    setImage(1, 1, 1, width, 1, height)

    logging.info('Acquire')
    startAcquisition()
        
    logging.info('Loop until acquisition finished')
    #waitForAcquisition();
    while getStatus() == ANDOR_ACQUIRING:
        time.sleep(0.1)

    logging.info('Get data')
    data = getAcquiredData(width, height)
    logging.info('Shape of data: %s', data.shape)
    
    hdu = fits.PrimaryHDU(data)
    hdu.writeto('image.fits', overwrite=True)

finally:
    logging.info('shutdown')
    shutdown()
    logging.info('done')

plt.imshow(data)
plt.show()
