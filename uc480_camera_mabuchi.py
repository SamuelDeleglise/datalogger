from instrumental import instrument, list_instruments
import instrumental as instr


class NoCameraError(Exception):
    pass


class UC480Camera:
    NO_CAMERA_ERROR = 'No camera loaded.'

    def __init__(self, camera_alias=None):
        self.cam = None
        self.load_camera(camera_alias)
        self.documentation_link = 'https://github.com/mabuchilab/Instrumental'

        self.exposure_time = 200
        self.timeout_time = 2000

    def load_camera(self, camera_alias):
        try:
            self.cam = instrument(camera_alias)
            self.close()
        except Exception as e:
            print(e)

    def close(self):
        if self.cam is None:
            raise NoCameraError(NO_CAMERA_ERROR)
        else:
            self.cam.close()

    def open(self):
        if self.cam is None:
            raise NoCameraError(NO_CAMERA_ERROR)
        else:
            self.cam._initialize()

    def take_camera_picture(self):
        """
        Times in milliseconds. Camera must be an instrumental object from the Mabuchi Instrumental package
        """
        if self.cam is not None:
            self.open()
                exposure_time = instr.Q_(self.exposure_time, units='ms')
            timeout_time = instr.Q_(self.timeout_time, units='ms')
            dump = self.cam.grab_image(timeout_time, exposure_time=exposure_time)  # needed for some reason to get it to work
            img = self.cam.grab_image(timeout_time, exposure_time=exposure_time)
            self.close()
            return img
        else:
            raise NoCameraError(NO_CAMERA_ERROR)

