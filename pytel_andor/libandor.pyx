cimport numpy as np
import numpy as np


cdef extern from "atmcdLXd.h":
    unsigned int GetAcquiredData16(unsigned short *arr, int size)
    unsigned int GetDetector(int *xpixels, int *ypixels)
    unsigned int GetStatus(int *status)
    unsigned int Initialize(char *dir)
    unsigned int SetAcquisitionMode(int mode)
    unsigned int SetExposureTime(float time)
    unsigned int SetImage(int hbin, int vbin, int hstart, int hend, int vstart, int vend)
    unsigned int SetReadMode(int mode)
    unsigned int SetShutter(int typ, int mode, int closingtime, int openingtime)
    unsigned int ShutDown()
    unsigned int StartAcquisition();
    unsigned int WaitForAcquisition();
  
    int DRV_SUCCESS
    int DRV_NOT_INITIALIZED
    int DRV_ACQUIRING 
    int DRV_ERROR_ACK
    int DRV_NOT_SUPPORTED
    int DRV_P1INVALID
    int DRV_P2INVALID
    int DRV_P3INVALID
    int DRV_P4INVALID
    int DRV_P5INVALID
    int DRV_P6INVALID
    int DRV_VXDNOTINSTALLED
    int DRV_INIERROR
    int DRV_COFERROR
    int DRV_FLEXERROR
    int DRV_ERROR_FILELOAD
    int DRV_ERROR_PAGELOCK
    int DRV_USBERROR
    int DRV_ERROR_NOCAMERA
    int DRV_NO_NEW_DATA
    int DRV_ACQUISITION_ERRORS
    int DRV_INVALID_FILTER
    int DRV_BINNING_ERROR
    int DRV_SPOOLSETUPERROR
    int DRV_IDLE
    int DRV_TEMPCYCLE
    int DRV_ACCUM_TIME_NOT_MET
    int DRV_KINETIC_TIME_NOT_MET
    int DRV_ACQ_BUFFER
    int DRV_ACQ_DOWNFIFO_FULL
    int DRV_SPOOLERROR


ANDOR_ACQUIRING = DRV_ACQUIRING


class AndorException(Exception):
    pass


def getAcquiredData(width, height):
    # create numpy array of given dimensions
    cdef np.ndarray[unsigned short, ndim=1] image = np.zeros((width * height), dtype=np.ushort)
    
    # call library
    res = GetAcquiredData16(<unsigned short*>image.data, width*height);
    print(res)
    
        # error checking
    if res != DRV_SUCCESS:
        raise AndorException({
                DRV_NOT_INITIALIZED: 'System not initialized.',
                DRV_ACQUIRING: 'Acquisition in progress.',
                DRV_ERROR_ACK: 'Unable to communicate with card.',
                DRV_P1INVALID: 'Invalid pointer (i.e. NULL).',
                DRV_P2INVALID: 'Array size isincorrect.',
                DRV_NO_NEW_DATA: 'No acquisition has taken place'
            }[res])
    
    # return image
    return image.reshape((height, width))

def getDetector():
    # define x and y
    cdef int x = 0
    cdef int y = 0
    
    # call library
    res = GetDetector(&x, &y)
    
    # error checking
    if res != DRV_SUCCESS:
        raise AndorException({
                DRV_NOT_INITIALIZED: 'System not initialized.'
            }[res])
    
    # no error, return detector size
    return x, y


def getStatus():
    # define status
    cdef int status = 0
    
    # call library
    res = GetStatus(&status)
    
    # error checking
    if res != DRV_SUCCESS:
        raise AndorException({
                DRV_NOT_INITIALIZED: 'System not initialized.'
            }[res])
    
    # no error, return status
    return status


def init(dir):
    # call library
    res = Initialize(bytes(dir, 'utf8'))
     
    # error checking
    if res != DRV_SUCCESS:
        raise AndorException({
                DRV_VXDNOTINSTALLED: 'VxD not loaded.',
                DRV_INIERROR: 'Unable to load "DETECTOR.INI".',
                DRV_COFERROR: 'Unable to load “*.COF".',
                DRV_FLEXERROR: 'Unable to load “*.RBF".',
                DRV_ERROR_ACK: 'Unable to communicate with card.',
                DRV_ERROR_FILELOAD: 'Unable to load “*.COF" or “*.RBF" files.',
                DRV_ERROR_PAGELOCK: 'Unable to acquire lock on requested memory.',
                DRV_USBERROR: 'Unable to detect USB device or not USB2.0.',
                DRV_ERROR_NOCAMERA: 'No camera found'
            }[res])


def setAcquisitionMode(mode):
    # call library
    res = SetAcquisitionMode(mode)
    
    # error checking
    if res != DRV_SUCCESS:
        raise AndorException({
                DRV_NOT_INITIALIZED: 'System not initialized.',
                DRV_ACQUIRING: 'Acquisition in progress.',
                DRV_P1INVALID: ' Acquisition Mode invalid.'
            }[res])
    
    
def setExposureTime(time):
    # call library
    res = SetExposureTime(time)
    
    # error checking
    if res != DRV_SUCCESS:
        raise AndorException({
                DRV_NOT_INITIALIZED: 'System not initialized.',
                DRV_ACQUIRING: 'Acquisition in progress.',
                DRV_P1INVALID: 'Exposure Time invalid.'
            }[res])
    
    
def setImage(hbin, vbin, hstart, hend, vstart, vend):
    # call library
    res = SetImage(hbin, vbin, hstart, hend, vstart, vend)
    
    # error checking
    if res != DRV_SUCCESS:
        raise AndorException({
                DRV_NOT_INITIALIZED: 'System not initialized.',
                DRV_ACQUIRING: 'Acquisition in progress.',
                DRV_P1INVALID: 'Binning parameters invalid.',
                DRV_P2INVALID: 'Binning parameters invalid.',
                DRV_P3INVALID: 'Sub-area co-ordinate is invalid.',
                DRV_P4INVALID: 'Sub-area co-ordinate is invalid.',
                DRV_P5INVALID: 'Sub-area co-ordinate is invalid.',
                DRV_P6INVALID: 'Sub-area co-ordinate is invalid.'
            }[res])

    
def setReadMode(mode):
    # call library
    res = SetReadMode(mode)
    
    # error checking
    if res != DRV_SUCCESS:
        raise AndorException({
                DRV_NOT_INITIALIZED: 'System not initialized.',
                DRV_ACQUIRING: 'Acquisition in progress.',
                DRV_P1INVALID: 'Invalid readout mode passed.'
            }[res])

def setShutter(typ, mode, closingtime, openingtime):
    # call library
    res = SetShutter(typ, mode, closingtime, openingtime)
    
    # error checking
    if res != DRV_SUCCESS:
        raise AndorException({
                DRV_NOT_INITIALIZED: 'System not initialized.',
                DRV_ACQUIRING: 'Acquisition in progress.',
                DRV_ERROR_ACK: 'Unable to communicate with card.',
                DRV_NOT_SUPPORTED: 'Camera does not support shutter control.',
                DRV_P1INVALID: 'Invalid TTL type.',
                DRV_P2INVALID: 'Invalid mode.',
                DRV_P3INVALID: 'Invalid time to open.',
                DRV_P4INVALID: 'Invalid time to close.'
            }[res])


def startAcquisition():
    # call library
    res = StartAcquisition()
    
    # error checking
    if res != DRV_SUCCESS:
        raise AndorException({
                DRV_NOT_INITIALIZED: 'System not initialized.',
                DRV_ACQUIRING: 'Acquisition in progress.',
                DRV_VXDNOTINSTALLED: 'VxD not loaded.',
                DRV_ERROR_ACK: 'Unable to communicate with card.',
                DRV_INIERROR: 'Error reading “DETECTOR.INI".',
                DRV_ACQUISITION_ERRORS: 'Acquisition settings invalid.',
                DRV_ERROR_PAGELOCK: 'Unable to allocate memory.',
                DRV_INVALID_FILTER: 'Filter not available for current acquisition.',
                DRV_BINNING_ERROR: 'Range not multiple of horizontal binning.',
                DRV_SPOOLSETUPERROR: 'Error with spool settings.'
            }[res])


def shutdown():
    ShutDown()


def waitForAcquisition():
    # call library
    res = WaitForAcquisition()
    
    # error checking
    if res != DRV_SUCCESS:
        raise AndorException({
                DRV_NOT_INITIALIZED: 'System not initialized.',
                DRV_NO_NEW_DATA: 'Non-Acquisition Event occured.',
            }[res])
