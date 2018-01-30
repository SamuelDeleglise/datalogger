import numpy as np
import ctypes as ct
import os, time, struct
import win32event

class UC480_CAMERA_INFO(ct.Structure):
    _fields_ = [
    ("dwCameraID", ct.c_uint32),
    ("dwDeviceID", ct.c_uint32),
    ("dwSensorID", ct.c_uint32),
    ("dwInUse", ct.c_uint32),
    ("SerNo", ct.c_char*16),
    ("Model", ct.c_char*16),
    ("dwStatus", ct.c_uint32),
    ("dwReserved", ct.c_uint32*15)]

class UC480_CAMERA_LIST(ct.Structure):

    _fields_=[]

    def __init__(self, number_of_elements):
        self._fields_ = [
        ("dwcount", ct.c_uint32),
        ("uci", UC480_CAMERA_INFO*number_of_elements)]
        self.dwcount = ct.c_uint32(number_of_elements)
        elems=(UC480_CAMERA_INFO * number_of_elements)()
        '''for i in range(number_of_elements):
            cam_inf = UC480_CAMERA_INFO()
            elems[i]=ct.pointer(cam_inf)'''
        self.uci=elems

class CAMINFO(ct.Structure):
    _fields_ = [
        ('SerNo', ct.c_char*12),
        ('ID', ct.c_char*20),
        ('Version', ct.c_char*10),
        ('Date', ct.c_char*12),
        ('Select', ct.c_ubyte),
        ('Type', ct.c_ubyte)]

class IMAGE_FORMAT_INFO(ct.Structure):
    _fields_ = [
        ('nFormatID', ct.c_int),
        ('nWidth', ct.c_uint),
        ('nHeight', ct.c_uint),
        ('nX0', ct.c_uint),
        ('nY0', ct.c_uint),
        ('nSupportedCaptureModes', ct.c_uint),
        ('nBinningMode', ct.c_uint),
        ('nSubsamplingMode', ct.c_uint),
        ('strFormatName', ct.c_char*64),
        ('dSensorScalerFactor', ct.c_double),
        ('nReserved', ct.c_uint*22)
    ]


class IMAGE_FORMAT_LIST(ct.Structure):
    _fields_ = [
        ('nSizeOfListEntry', ct.c_uint),
        ('nNumListElements', ct.c_uint),
        ('nReserved', ct.c_uint*4),
        ('FormatInfo', IMAGE_FORMAT_INFO*1)
    ]

    def __init__(self, number_of_elements):
        self.nNumListElements = number_of_elements
        self.nSizeOfListEntry = ct.sizeOf(IMAGE_FORMAT_INFO)


class IMAGE_FILE_PARAMS(ct.Structure):

    _fields_ = [
        ('pwchFileName', ct.c_wchar_p),
        ('nFileType', ct.c_uint),
        ('nQuality', ct.c_uint),
        ('ppcImageMem', ct.POINTER(ct.POINTER(ct.c_char))),
        ('pnImageID', ct.POINTER(ct.c_uint)),
        ('reserved', ct.c_byte*32)
    ]

class uc480_CAPTURE_STATUS_INFO(ct.Structure):
    _fields_ = [
        ('dwCapStatusCnt_Total', ct.c_uint32),
        ('reserved', ct.c_byte*60),
        ('adwCapStatusCnt_Detail', ct.c_uint32*256)
    ]

class SENSORINFO(ct.Structure):
    _fields_ = [
        ('SensorID', ct.c_uint16),
        ('strSensorName', ct.c_char*32),
        ('nColorMode', ct.c_char),
        ('nMaxWidth', ct.c_uint32),
        ('nMaxHeight', ct.c_uint32),
        ('bMasterGain', ct.c_bool),
        ('bRGain', ct.c_bool),
        ('bGGain', ct.c_bool),
        ('bBGain', ct.c_bool),
        ('bGlobShutter', ct.c_bool),
        ('wPixelSize', ct.c_uint16),
        ('Reserved', ct.c_char*14)
    ]


class Camera:

    def __init__(self, width, height):
        self.IS_SET_TRIG_OFF = 0x0000
        self.IS_SET_EVENT_FRAME = 2
        self.IS_SET_EVENT_SEQ = 5
        self.IS_SENSOR_D1024G13C = 0x0081
        self.IS_COLORMODE_BAYER = 2
        self.IS_COLORMODE_MONOCHROME = 1
        self.IS_GET_SUPPORTED_GAINBOOST = 0x0002
        self.IS_SET_GAINBOOST_OFF = 0x0000
        self.IS_SET_GAINBOOST_ON = 0x0001
        self.IS_GET_MASTER_GAIN_FACTOR = 0x8000
        self.IS_SET_MASTER_GAIN_FACTOR = 0x8004
        self.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MIN = 3
        self.IS_EXPOSURE_CMD_GET_EXPOSURE_DEFAULT = 2
        self.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MAX = 4
        self.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_INC = 5
        self.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE = 6
        self.IS_EXPOSURE_CMD_GET_EXPOSURE = 7
        self.IS_EXPOSURE_CMD_SET_EXPOSURE = 12
        self.IS_EXPOSURE_CAP_EXPOSURE = 0x00000001
        self.IS_EXPOSURE_CAP_FINE_INCREMENT = 0x00000002
        self.IS_EXPOSURE_CAP_LONG_EXPOSURE = 0x00000004
        self.IS_EXPOSURE_CAP_DUAL_EXPOSURE = 0x00000008
        self.IS_EXPOSURE_CMD_GET_CAPS = 1
        self.CAPTMODE_SINGLE = 0x00000001
        self.CAPTMODE_FREERUN = 0x00000002
        self.CAPTMODE_TRIGGER_SOFT_SINGLE = 0x00000010
        self.CAPTMODE_TRIGGER_SOFT_CONTINUOUS = 0x00000020
        self.CAPTMODE_TRIGGER_HW_SINGLE = 0x00000100
        self.CAPTMODE_TRIGGER_HW_CONTINUOUS = 0x00000200
        self.IS_IGNORE_PARAMETER = -1
        self.IS_SET_CM_RGB32 = 0
        self.IS_CM_ORDER_RGB = 0x0080
        self.IS_CM_FORMAT_PACKED = 0x0000
        self.IS_CM_RGBA8_PACKED = self.IS_SET_CM_RGB32 | self.IS_CM_ORDER_RGB | self.IS_CM_FORMAT_PACKED
        self.IS_CM_MONO16 = 28
        self.IS_CAPTURE_STATUS_INFO_CMD_GET = 2
        self.IS_CAPTURE_STATUS_INFO_CMD_RESET = 1
        self.IS_WAIT = 0x0001
        self.IS_DONT_WAIT = 0x0000
        self.IS_IMG_PNG = 2
        self.IS_IMG_JPG = 1
        self.IS_IMG_BMP = 0
        self.IS_IMG_RAW = 4
        self.IS_IMG_TIF = 8
        self.IS_IMAGE_FILE_CMD_LOAD = 1
        self.IS_IMAGE_FILE_CMD_SAVE = 2
        self.IMGFRMT_CMD_GET_NUM_ENTRIES = 1
        self.IMGFRMT_CMD_GET_LIST = 2
        self.IS_SET_TRIGGER_SOFTWARE = 0x1000|0x0008
        self.IS_GET_COLOR_MODE = 0x8000
        self.IS_CM_RGB8_PACKED = 1
        if struct.calcsize("P") * 8 == 64:
            self.dllpath = os.path.join("C:\Windows\System32","uc480_64.dll")
        else:
            self.dllpath = os.path.join("C:\Windows\System32","uc480.dll")
        self.dll = ct.cdll.LoadLibrary(self.dllpath)
        self._is_capturing_video = False
        self.number_of_camera = self.number_of_camera_connected()
        self.camera_list = UC480_CAMERA_LIST(self.number_of_camera)
        self.get_camera_list(ct.pointer(self.camera_list))
        self.camera_ID = self.camera_list.uci[0].dwCameraID
        self.camera_handle = ct.c_int(self.camera_ID)
        self._in_use = False
        self.init_camera(ct.pointer(self.camera_handle))
        self.set_color_mode(self.IS_CM_RGBA8_PACKED)
        self.set_error_report(1)
        self.get_camera_info()
        self._event_raised=False
        self.get_sensor_info()
        self.get_exposure_range()
        self.color_depth = ct.c_int()
        self.color_mode = ct.c_int()
        self.get_color_depth()
        self.width = width
        self.height = height
        self.pid = ct.c_int()
        self.increment = ct.c_int()
        line = width*np.int((self.color_depth.value+7)/8)
        if line%4==0:
            self.adjust = 0
        else:
            self.adjust = 4-line%4
        self.ppcImgMem = ct.pointer((ct.c_char*((width*np.int((self.color_depth.value+7)/8)+self.adjust)*height))())
        self.allocate_memory(ct.pointer(self.ppcImgMem), ct.pointer(self.pid))
        self._event_enabled = False
        self.init_events()

        self.set_image_mem()
        self.get_line_increment(ct.pointer(self.increment))
        self.set_trigger_mode(self.IS_SET_TRIGGER_SOFTWARE)
        self.add_to_sequence()
        self._is_queue_active = False
        self.imageID = ct.c_int()
        '''
        self.number_of_image_formats = ct.c_uint()
        self.get_image_format_list_size(ct.pointer(self.number_of_image_formats))
        nSizeOfParam = ct.sizeof(IMAGE_FORMAT_LIST)+ct.sizeof(IMAGE_FORMAT_INFO*(self.number_of_image_formats.value-1))
        ptr = (ct.c_byte*nSizeOfParam)()
        self.image_format_list = ct.cast(ct.pointer(ptr), ct.POINTER(IMAGE_FORMAT_LIST))
        self.image_format_list.contents.nSizeOfListEntry = ct.sizeof(IMAGE_FORMAT_INFO)
        self.image_format_list.contents.nNumListElements = self.number_of_image_formats
        self.get_image_format_list(self.image_format_list, nSizeOfParam)
        ptr = ct.pointer(self.image_format_list.contents.FormatInfo)
        ct.cast(ptr, ct.POINTER(IMAGE_FORMAT_INFO*(self.number_of_image_formats.value)))
        self.image_formats = ptr
        '''
        self.get_image_format_list()
        self.pcMem = ct.pointer((ct.c_char*((self.width*np.int((self.color_depth.value+7)/8)+self.adjust)*self.height))())
        self.capture_video(self.IS_WAIT)

    def live_mode(self):
        if self._is_capturing_video:
            self.stop_live_video(self.IS_WAIT)
        if self._is_queue_active:
            self.exit_image_queue()
        self.set_trigger_mode(self.IS_SET_TRIG_OFF)
        self.enable_events()
        self.capture_video(self.IS_WAIT)

    def init_events(self):
        #self._seq_event = win32event.CreateEvent(None, False, False, '')
        self._frame_event = win32event.CreateEvent(None, True, False, '')  # Don't auto-reset
        #res = self.dll.is_InitEvent(self.camera_handle, self._seq_event.handle, self.IS_SET_EVENT_SEQ)
        #assert res==0, 'is_InitEvent res='+str(res)
        res = self.dll.is_InitEvent(self.camera_handle, self._frame_event.handle, self.IS_SET_EVENT_FRAME)
        assert res==0, 'is_InitEvent res='+str(res)
        self._is_event_initialized = True

    def exit_event(self):
        if self._is_event_initialized:
            res = self.dll.is_ExitEvent(self.camera_handle, self.IS_SET_EVENT_FRAME)
            assert res==0, "is_ExitEvent res = "+str(res)
            self._is_event_initialized=False

    def __del__(self):
        self.exit() # In case someone forgot to exit()

    def enable_events(self):
        #res = self.dll.is_EnableEvent(self.camera_handle, self.IS_SET_EVENT_SEQ)
        #assert res==0, 'is_EnableEvent res='+str(res)
        res = self.dll.is_EnableEvent(self.camera_handle, self.IS_SET_EVENT_FRAME)
        assert res==0, 'is_EnableEvent res='+str(res)
        self._event_enabled=True

    def disable_events(self):
        #res = self.dll.is_DisableEvent(self.camera_handle, self.IS_SET_EVENT_SEQ)
        #assert res==0, 'is_DisableEvent res='+str(res)
        res = self.dll.is_DisableEvent(self.camera_handle, self.IS_SET_EVENT_FRAME)
        assert res==0, 'is_DisableEvent res='+str(res)
        self._event_enabled=False

    def get_image_format_list(self):
        self.number_of_image_formats = ct.c_uint()
        self.get_image_format_list_size(ct.pointer(self.number_of_image_formats))
        nSizeOfParam = ct.sizeof(IMAGE_FORMAT_LIST)+ct.sizeof(IMAGE_FORMAT_INFO*(self.number_of_image_formats.value-1))
        ptr = (ct.c_byte*nSizeOfParam)()
        self.image_format_list = ct.cast(ct.pointer(ptr), ct.POINTER(IMAGE_FORMAT_LIST))
        self.image_format_list.contents.nSizeOfListEntry = ct.sizeof(IMAGE_FORMAT_INFO)
        self.image_format_list.contents.nNumListElements = self.number_of_image_formats
        res = self.dll.is_ImageFormat(self.camera_handle, self.IMGFRMT_CMD_GET_LIST, self.image_format_list, nSizeOfParam)
        ptr = ct.pointer(self.image_format_list.contents.FormatInfo)
        ct.cast(ptr, ct.POINTER(IMAGE_FORMAT_INFO*(self.number_of_image_formats.value)))
        self.image_formats = ptr
        assert res==0,'is_ImageFormat res='+str(res)

    def number_of_camera_connected(self):
        b=ct.POINTER(ct.c_int)(ct.c_int())
        if self.dll.is_GetNumberOfCameras(b)==0:
            return np.frombuffer(ct.string_at(b,4), dtype=int)[0]
        else:
            raise ValueError('The argument is not a pointer to int !')

    def get_camera_list(self, p_camera_list):
        res = self.dll.is_GetCameraList(p_camera_list)
        assert res==0,  "is_GetCameraList res = "+str(res)

    def init_camera(self, p_camera_handle):
        res= self.dll.is_InitCamera(p_camera_handle, None)
        assert res==0, "is_InitCamera res = "+str(res)
        self._in_use=True

    def exit_camera(self):
        res= self.dll.is_ExitCamera(self.camera_handle)
        assert res==0, "is_ExitCamera res = "+str(res)
        self._in_use=False

    def find_nearest(self, arr, val):
        idx = (np.abs(arr-val)).argmin()
        return arr[idx]

    def get_camera_info(self):
        self.camera_info = CAMINFO()
        res=self.dll.is_GetCameraInfo(self.camera_handle, ct.pointer(self.camera_info))
        assert res==0, "is_GetCameraInfo res = "+str(res)

    def exit(self):
        if self._event_enabled:
            self.disable_events()
        if self._is_event_initialized:
            self.exit_event()
        #res = self.dll.is_ExitEvent(self.camera_handle, self.IS_SET_EVENT_SEQ)
        #assert res==0, "is_ExitEvent res = "+str(res)
        if self._in_use:
            self.exit_camera()

    def wait_for_frame(self, timeout=None):
        timeout_ms = win32event.INFINITE if timeout is None else int(timeout)
        ret = win32event.WaitForSingleObject(self._frame_event, timeout_ms)
        win32event.ResetEvent(self._frame_event)
        if ret == win32event.WAIT_TIMEOUT:
            return False
        elif ret != win32event.WAIT_OBJECT_0:
            raise Error("Failed to grab image: Windows event return code 0x{:x}".format(ret))
        self._event_raised=True
        return True

    def get_color_depth(self):
        res = self.dll.is_GetColorDepth(self.camera_handle,ct.pointer(self.color_depth), ct.pointer(self.color_mode))
        assert res==0, 'is_GetColorDepth res = '+str(res)

    def allocate_memory(self, p_ppcImgMem, p_pid):
        width = ct.c_int(self.width)
        height = ct.c_int(self.height)
        bitspixel = self.color_depth
        res = self.dll.is_AllocImageMem(self.camera_handle, width, height, bitspixel, p_ppcImgMem, p_pid)
        assert res==0, 'is_AllocImageMem res ='+str(res)

    def set_image_mem(self):
        res = self.dll.is_SetImageMem(self.camera_handle, self.ppcImgMem, self.pid)
        assert res==0, 'is_SetImageMem res = '+str(res)

    def free_image_mem(self):
        res = self.dll.is_FreeImageMem(self.camera_handle, self.ppcImgMem, self.pid)
        assert res==0, 'is_FreeImageMem res = '+str(res)

    def set_trigger_mode(self, value):
        res = self.dll.is_SetExternalTrigger(self.camera_handle, ct.c_int(value))
        assert res==0, 'is_SetExternalTrigger res = '+str(res)

    def freeze_video(self):
        res = self.dll.is_FreezeVideo(self.camera_handle, self.IS_WAIT)
        assert res==0, 'is_FreezeVideo res = '+str(res)

    def set_error_report(self, val):
        res = self.dll.is_SetErrorReport(self.camera_handle, val)
        assert res==0, 'is_SetErrorReport res='+str(res)

    @property
    def exposure_time(self):
        param = ct.c_double()
        res = self.dll.is_Exposure(self.camera_handle, self.IS_EXPOSURE_CMD_GET_EXPOSURE, ct.pointer(param), ct.c_uint(8))
        assert res==0, 'is_Exposure res='+str(res)
        return param

    @exposure_time.setter
    def exposure_time(self, val):
        value = self.find_nearest(self.exposure_range, val)
        value = ct.c_double(value)
        nSizeOfParams = ct.c_uint(8)
        res = self.dll.is_Exposure(self.camera_handle, self.IS_EXPOSURE_CMD_SET_EXPOSURE, ct.pointer(value), nSizeOfParams)
        assert res==0, 'is_Exposure res='+str(res)
        print(value)

    @property
    def master_gain(self):
        return self.dll.is_SetHWGainFactor(self.camera_handle, self.IS_GET_MASTER_GAIN_FACTOR, 100)

    @master_gain.setter
    def master_gain(self, val):
        self.dll.is_SetHWGainFactor(self.camera_handle, self.IS_SET_MASTER_GAIN_FACTOR, ct.c_uint(val))

    def get_exposure_range(self):
        exposure_range = (ct.c_double*3)()
        nSizeOfParams = ct.c_uint(24)
        res = self.dll.is_Exposure(self.camera_handle, self.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE, ct.pointer(exposure_range), nSizeOfParams)
        assert res==0, 'is_Exposure res='+str(res)
        self.min_exposure=exposure_range[0]
        self.max_exposure=exposure_range[1]
        self.exposure_increment=exposure_range[2]
        self.exposure_range = np.arange(self.min_exposure, self.max_exposure, self.exposure_increment)

    def set_exposure_time(self, val):
        param = ct.c_double(val)
        res = self.dll.is_Exposure(self.camera_handle, self.IS_EXPOSURE_CMD_SET_EXPOSURE, ct.pointer(param), ct.c_uint(8))
        assert res==0, 'is_Exposure res='+str(res)
        return param

    def set_io(self):
        nMode = ct.c_uint(2)
        res = self.dll.is_IO(self.camera_handle, 20, ct.cast(ct.pointer(nMode), ct.c_void_p), ct.sizeof(nMode))
        assert res==0, 'is_IO res='+str(res)

    def get_line_increment(self, p_Pitch):
        res = self.dll.is_GetImageMemPitch(self.camera_handle, p_Pitch)
        assert res==0, 'is_GetImageMemPitchh res='+str(res)

    def get_image_format_list_size(self, p_Param):
        res = self.dll.is_ImageFormat(self.camera_handle, self.IMGFRMT_CMD_GET_NUM_ENTRIES, p_Param, ct.c_uint(4))
        assert res==0, 'is_ImageFormat res='+str(res)

    def add_to_sequence(self):
        res = self.dll.is_AddToSequence(self.camera_handle, self.ppcImgMem, self.pid)
        assert res==0, 'is_AddToSequence res='+str(res)

    def init_Image_Queue(self):
        res = self.dll.is_InitImageQueue(self.camera_handle, 0)
        assert res==0, 'is_InitImageQueue res='+str(res)
        self._is_queue_active=True

    def wait_For_Next_Image(self, timeout, ppcMem, pimageID):
        res = self.dll.is_WaitForNextImage(self.camera_handle, timeout, ppcMem, pimageID)
        assert res==0, 'is_WaitForNextImage res='+str(res)

    def capture_video(self, wait):
        res = self.dll.is_CaptureVideo(self.camera_handle, wait)
        assert res==0, 'is_CaptureVideo res='+str(res)
        self._is_capturing_video=True

    def stop_live_video(self, wait):
        res = self.dll.is_StopLiveVideo(self.camera_handle, wait)
        assert res==0, 'is_StopLiveVideo res='+str(res)
        self._is_capturing_video=False

    def unlock_seq_buf(self):
        res = self.dll.is_UnlockSeqBuf(self.camera_handle, self.imageID, self.pcMem)
        #res = self.dll.is_UnlockSeqBuf(self.camera_handle, self.IS_IGNORE_PARAMETER, self.pcMem)
        assert res==0, 'is_UnlockSeqBuf res='+str(res)

    def lock_seq_buf(self):
        res = self.dll.is_LockSeqBuf(self.camera_handle, self.imageID, self.pcMem)
        # res = self.dll.is_LockSeqBuf(self.camera_handle, self.IS_IGNORE_PARAMETER, self.pcMem)
        assert res==0, 'is_LockSeqBuf res='+str(res)

    def get_picture(self):
        self.init_Image_Queue()
        self.pcMem = ct.pointer((ct.c_char*((self.width*np.int((self.color_depth.value+7)/8)+self.adjust)*self.height))())
        self.wait_For_Next_Image(3000, ct.pointer(self.pcMem), ct.pointer(self.imageID))
        self.unlock_seq_buf()
        self.exit_image_queue()
        data = ct.string_at(self.pcMem, self.height*self.increment.value*ct.sizeof(ct.c_char))

        red = np.frombuffer(data[0::4], dtype=np.byte)
        green = np.frombuffer(data[1::4], dtype=np.byte)
        blue = np.frombuffer(data[2::4], dtype=np.byte)
        grey = red+green+blue
        res = np.reshape(grey, [self.height, self.width])
        return res

    def get_picture_rgba(self, single=True):
        if not self._is_queue_active and not self._event_enabled:
            self.init_Image_Queue()
        self.pcMem = ct.pointer((ct.c_char*((self.width*np.int((self.color_depth.value+7)/8)+self.adjust)*self.height))())
        if not self._event_enabled:
            self.wait_For_Next_Image(3000, ct.pointer(self.pcMem), ct.pointer(self.imageID))
            self.unlock_seq_buf()
        else:
            if self._event_raised:
                data = ct.string_at(self.pcMem, self.height*self.increment.value*ct.sizeof(ct.c_char))
            else:
                self.wait_for_frame()
                data = ct.string_at(self.pcMem, self.height*self.increment.value*ct.sizeof(ct.c_char))

        self._event_raised=False
        if single:
            self.exit_image_queue()
        data = ct.string_at(self.pcMem, self.height*self.increment.value*ct.sizeof(ct.c_char))

        red = np.reshape(np.frombuffer(data[0::4], dtype=np.byte),[self.height, self.width])
        green = np.reshape(np.frombuffer(data[1::4], dtype=np.byte),[self.height, self.width])
        blue = np.reshape(np.frombuffer(data[2::4], dtype=np.byte), [self.height, self.width])
        alpha = np.reshape(np.frombuffer(data[3::4], dtype=np.byte), [self.height, self.width])
        return red, green, blue, alpha

    def get_picture_cv2_format(self, single=True):
        # image format: RGBA8_PACKED. Corresponds to bgr in cv2. Returns the numbers in 'uint8' type, supported by
        # the contrats detection code of pyinsturments
        r, g, b, a = self.get_picture_rgba(single=single)
        res = np.empty([self.height, self.width, 4]).astype('int8')
        factor = 8
        res[:, :, 0] = b*factor
        res[:, :, 1] = g*factor
        res[:, :, 2] = r*factor
        res[:, :, 3] = a*factor
        res = res[:, :, :3].astype('uint8')  # not sure why, but certainly need to remove a to analyse contrasts.
        return res

    def get_color_mode(self):
        return self.dll.is_SetColorMode(self.camera_handle, self.IS_GET_COLOR_MODE)

    def set_color_mode(self, val):
        res = self.dll.is_SetColorMode(self.camera_handle, val)
        assert res==0, 'is_SetColorMode res='+str(res)

    def exit_image_queue(self):
        if self._is_queue_active:
            res = self.dll.is_ExitImageQueue(self.camera_handle)
            assert res==0, 'is_ExitImageQueue res='+str(res)
            self._is_queue_active=False

    def get_sensor_info(self):
        self.sensor_info = SENSORINFO()
        res = self.dll.is_GetSensorInfo(self.camera_handle, ct.pointer(self.sensor_info))
        assert res==0, 'is_GetSensorInfo res='+str(res)

    def get_exposure_caps(self):
        nCaps = ct.c_uint()
        nSizeOfParams = ct.c_uint(4)
        res = self.dll.is_Exposure(self.camera_handle, self.IS_EXPOSURE_CMD_GET_CAPS, ct.pointer(self.nCaps), nSizeOfParams)
        assert res==0, 'is_Exposure res='+str(res)
        self.nCaps = nCaps.value
        return self.nCaps

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.exit()

