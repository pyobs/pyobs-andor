import logging
import math
import threading
from datetime import datetime
import time
import numpy as np
from astropy.io import fits

from pytel.interfaces import ICamera, ICameraWindow, ICameraBinning, ICooling
from pytel.modules.camera.basecamera import BaseCamera, CameraException
from .libandor import Initialize, Shutdown


log = logging.getLogger(__name__)


class AndorCamera(BaseCamera, ICamera, ICameraWindow, ICameraBinning, ICooling):
    def __init__(self, *args, **kwargs):
        BaseCamera.__init__(self, *args, **kwargs)

        # variables
        self._dev_domain = None
        self._dev_file = None
        self._dev_name = None
        self._connected = False
        self._dev = None
        self._temp_setpoint = None

        # window and binning
        self._window = None
        self._binning = None
        self._window_dirty = True

    def open(self) -> bool:
        # open base
        if not BaseCamera.open(self):
            return False

        # already open?
        if self._dev is not None:
            return False

        # create list of USB cameras
        fli.CreateList(fli.FLIDOMAIN_USB | fli.FLIDEVICE_CAMERA)

        # fetch first
        # return values are something like: (258 /dev/fliusb1 ProLine PL230)
        self._dev_domain, self._dev_file, self._dev_name = fli.ListFirst()

        # clean up list
        fli.DeleteList()

        # open connection
        log.info('Opening connection to "%s" at %s...', self._dev_name, self._dev_file)
        self._dev = fli.Open(self._dev_file, self._dev_domain)

        # get window and binning from camera
        self._window = self._get_window()
        self._binning = self._get_binning()
        self._window_dirty = False

        # set cooling
        self._temp_setpoint = None
        self.set_cooling(True, self.config['setpoint'])

        # success
        return True

    def close(self):
        # close base
        BaseCamera.close(self)

        # not open?
        if self._dev is not None:
            # close connection
            fli.Close(self._dev)
            self._dev = None

    def _check_dev(self):
        # not connected?
        if self._dev is None:
            raise CameraException("Not connected to camera.")

    @classmethod
    def default_config(cls):
        cfg = super(FliCamera, cls).default_config()
        cfg['setpoint'] = -20.
        return cfg

    def get_full_frame(self, *args, **kwargs) -> dict:
        self._check_dev()
        size = fli.GetVisibleArea(self._dev)
        return {'left': size[0], 'top': size[1], 'width': size[2]-size[0], 'height': size[3]-size[1]}

    def _get_window(self) -> dict:
        self._check_dev()
        dim = fli.GetReadoutDimensions(self._dev)
        return {'left': dim[1], 'top': dim[4], 'width': dim[0], 'height': dim[3]}

    def _get_binning(self) -> dict:
        self._check_dev()
        dim = fli.GetReadoutDimensions(self._dev)
        return {'x': dim[2], 'y': dim[5]}

    def get_window(self, *args, **kwargs) -> dict:
        return self._window

    def get_binning(self, *args, **kwargs) -> dict:
        return self._binning

    def set_window(self, left: int, top: int, width: int, height: int, *args, **kwargs) -> bool:
        self._window = {'left': int(left), 'top': int(top), 'width': int(width), 'height': int(height)}
        self._window_dirty = True
        log.info('Setting window to %dx%d at %d,%d...', width, height, left, top)
        return True

    def set_binning(self, x: int, y: int, *args, **kwargs) -> bool:
        self._binning = {'x': int(x), 'y': int(y)}
        self._window_dirty = True
        log.info('Setting binning to %dx%d...', x, y)
        return True

    def _set_window_binning(self):
        if self._window_dirty:
            # check device
            self._check_dev()

            # set binning
            log.info("Set binning to %dx%d.", self._binning['x'], self._binning['y'])
            fli.SetHBin(self._dev, int(self._binning['x']))
            fli.SetVBin(self._dev, int(self._binning['y']))

            # set window, divide width/height by binning, from libfli:
            # "Note that the given lower-right coordinate must take into account the horizontal and
            # vertical bin factor settings, but the upper-left coordinate is absolute."
            width = int(math.floor(self._window['width']) / self._binning['x'])
            height = int(math.floor(self._window['height']) / self._binning['y'])
            log.info("Set window to %dx%d (binned %dx%d) at %d,%d.",
                         self._window['width'], self._window['height'],
                         width, height,
                         self._window['left'], self._window['top'])
            fli.SetImageArea(self._dev, int(self._window['left']), int(self._window['top']),
                             int(self._window['left'] + width), int(self._window['top'] + height))

            # cleaned!
            self._window_dirty = False

    def _expose(self, exposure_time: int, open_shutter: bool, abort_event: threading.Event) -> fits.ImageHDU:
        self._check_dev()

        # set window/binning, if necessary
        self._set_window_binning()

        # set some stuff
        self._camera_status = ICamera.CameraStatus.EXPOSING
        fli.SetTDI(self._dev, 0, 0)
        fli.SetExposureTime(self._dev, int(exposure_time))
        fli.SetFrameType(self._dev, fli.FLI_FRAME_TYPE_NORMAL if open_shutter else fli.FLI_FRAME_TYPE_DARK)

        # get date obs
        log.info('Starting exposure with %s shutter for %.2f seconds...',
                 'open' if open_shutter else 'closed', exposure_time / 1000.)
        date_obs = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")

        # do exposure
        fli.ExposeFrame(self._dev)

        # wait for exposure to finish
        while True:
            # aborted?
            if abort_event.is_set():
                log.warning('Aborted exposure.')
                return None

            # get status
            camera_status = fli.GetDeviceStatus(self._dev)
            remaining_exposure = fli.GetExposureStatus(self._dev)

            # check it
            if (camera_status == fli.FLI_CAMERA_STATUS_UNKNOWN and remaining_exposure == 0) or \
                    (camera_status != fli.FLI_CAMERA_STATUS_UNKNOWN and camera_status & fli.FLI_CAMERA_DATA_READY):
                break
            else:
                # sleep a little
                time.sleep(0.2)

        # readout
        log.info('Exposure finished, reading out...')
        self._camera_status = ICamera.CameraStatus.READOUT
        width = int(math.floor(self._window['width'] / self._binning['x']))
        height = int(math.floor(self._window['height'] / self._binning['y']))
        img = np.zeros((height, width), dtype=np.uint16)
        for row in range(height):
            img[row, :] = fli.GrabRow(self._dev, width)

        # create FITS image and set header
        hdu = fits.PrimaryHDU(img)
        hdu.header['DATE-OBS'] = (date_obs, 'Date and time of start of exposure')
        hdu.header['EXPTIME'] = (exposure_time / 1000., 'Exposure time [s]')
        hdu.header['DET-TEMP'] = (fli.ReadTemperature(self._dev, fli.FLI_TEMPERATURE_CCD), 'CCD temperature [C]')
        hdu.header['DET-COOL'] = (fli.GetCoolerPower(self._dev), 'Cooler power [percent]')
        hdu.header['DET-TSET'] = (self._temp_setpoint, 'Cooler setpoint [C]')

        # instrument and detector
        hdu.header['INSTRUME'] = (self._dev_name, 'Name of instrument')

        # binning
        hdu.header['XBINNING'] = hdu.header['DET-BIN1'] = (self._binning['x'], 'Binning factor used on X axis')
        hdu.header['YBINNING'] = hdu.header['DET-BIN2'] = (self._binning['y'], 'Binning factor used on Y axis')

        # window
        hdu.header['XORGSUBF'] = (self._window['left'], 'Subframe origin on X axis')
        hdu.header['YORGSUBF'] = (self._window['top'], 'Subframe origin on Y axis')

        # statistics
        hdu.header['DATAMIN'] = (float(np.min(img)), 'Minimum data value')
        hdu.header['DATAMAX'] = (float(np.max(img)), 'Maximum data value')
        hdu.header['DATAMEAN'] = (float(np.mean(img)), 'Mean data value')

        # biassec/trimsec
        full = self.get_full_frame()
        self.set_biassec_trimsec(hdu.header, full['left'], full['top'], full['width'], full['height'])

        # return FITS image
        log.info('Readout finished.')
        self._camera_status = ICamera.CameraStatus.IDLE
        return hdu

    def _abort_exposure(self) -> bool:
        """Aborts the current exposure.

        Returns:
            bool: True if successful, otherwise False.
        """
        self._check_dev()
        fli.CancelExposure(self._dev)
        self._camera_status = ICamera.CameraStatus.IDLE
        return True

    def status(self, *args, **kwargs) -> dict:
        self._check_dev()

        # get status from parent
        s = super().status()

        # add cooling stuff
        s['ICooling'] = {
            'Enabled': self._temp_setpoint is not None,
            'SetPoint': self._temp_setpoint,
            'Power': fli.GetCoolerPower(self._dev),
            'Temperatures': {
                'CCD': fli.ReadTemperature(self._dev, fli.FLI_TEMPERATURE_CCD),
                'Base': fli.ReadTemperature(self._dev, fli.FLI_TEMPERATURE_BASE)
            }
        }

        # finished
        return s

    def set_cooling(self, enabled: bool, setpoint: float, *args, **kwargs) -> bool:
        self._check_dev()

        # log
        if enabled:
            log.info('Enabling cooling with a setpoint of %.2f°C...', setpoint)
        else:
            log.info('Disabling cooling and setting setpoint to 20°C...')

        # if not enabled, set setpoint to None
        self._temp_setpoint = setpoint if enabled else None

        # set setpoint
        fli.SetTemperature(self._dev, float(setpoint) if setpoint is not None else 20.)
        return True
