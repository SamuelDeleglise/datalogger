import ctypes as ct
import time


class KCubeManager:
    DEVICE_MANAGER_DLL_PATH = "C:/Program Files/Thorlabs/Kinesis/Thorlabs.MotionControl.DeviceManager.dll"
    SERVO_DLL_PATH = "C:/Program Files/Thorlabs/Kinesis/Thorlabs.MotionControl.KCube.DCServo.dll"
    MOVEMENT_SLEEP_TIME = 0.02  # seconds to wait for movement detection

    def __init__(self):
        self.device_manager_dll = ct.WinDLL(self.DEVICE_MANAGER_DLL_PATH)  # required to load self.dll
        self.dll = ct.WinDLL(self.SERVO_DLL_PATH)

        self.check(self.dll.TLI_BuildDeviceList())  # startup check
        self.device_no = self.dll.TLI_GetDeviceListSize()

        self.ascii_serials = (ct.c_char*100)(100)
        self.check(self.dll.TLI_GetDeviceListByTypeExt(self.ascii_serials, 100, 27))
        self.ascii_serials = self.ascii_serials.value.decode('ascii')
        self.ascii_serials = self.ascii_serials.split(',')

        self.b_serials = []  # in binary format
        for i in range(self.device_no):
            self.b_serials.append(self.ascii_serials[i].encode())

        self.open_motors = dict()

    @staticmethod
    def check(val):
        if val != 0:
            raise ValueError("Function returned error code %i"%val)

    def connect(self, servo_serial, servo_name='MyServos'):
        exists = 0
        for name, motor in self.open_motors.items():
            if motor.serial == servo_serial:
                exists = 1
                found_name = name
                print('Serial {} already saved as {}'.format(servo_serial, found_name))
        if not exists:
            self.check(self.dll.CC_Open(servo_serial))
            self.open_motors[servo_name] = Motor(servo_serial)
            self.set_jog_parameters(servo_name)

    def close(self, servo_name):
        self.dll.CC_Close(self.open_motors[servo_name].serial)
        self.open_motors.pop(servo_name)

    def rename(self, old_name, new_name):
        if old_name in self.open_motors.keys():
            serial = self.open_motors[old_name].serial
            self.open_motors.pop(old_name)
            self.open_motors[new_name] = Motor(serial)
        else:
            print('{} is not a motor name. \nAvailable names are: {}'.format(old_name, self.open_motors.keys()))

    def get_tick_position(self, servo_name):
        serial = self.open_motors[servo_name].serial
        self.dll.CC_RequestPosition(serial)
        tick_pos = self.dll.CC_GetPosition(serial)
        return tick_pos

    def get_position(self, servo_name):
        # in µm
        tick_pos = self.get_tick_position(servo_name)
        pos = tick_pos * self.open_motors[servo_name].UM_PER_COUNT
        return pos

    def home(self, servo_name):
        self.dll.CC_Home(self.open_motors[servo_name].serial)

    def move_to_position(self, servo_name, tick_pos):
        """
        Moves to a given position (in device units)
        :param servo_name:
        :param tick_pos:
        """
        self.dll.CC_MoveToPosition(self.open_motors[servo_name].serial, tick_pos)

    def jog(self, servo_name, dist):
        """
        Moves forward (or backward) by the given distance (in µm)
        :param servo_name:
        :param dist:
        """
        tick_pos = self.get_tick_position(servo_name)
        tick_jog = int(dist/self.open_motors[servo_name].UM_PER_COUNT)
        self.move_to_position(servo_name, tick_pos+tick_jog)

    def is_moving(self, servo_name):
        pos1 = self.get_tick_position(servo_name)
        time.sleep(self.MOVEMENT_SLEEP_TIME)
        pos2 = self.get_tick_position(servo_name)
        if pos1-pos2 == 0:
            return False
        else:
            return True

    def change_direction(self, servo_name):
        """
        Moves the servo in one direction by twice the backlash, then in the other by that amount. This is to overcome
        the hysteresis of movement. The direction of movement needs to have been specified at some point correctly
        first.

        :param servo_name:
        """
        motor = self.open_motors[servo_name]
        if motor.direction:
            # MOVE FORWARD THEN BACKWARD
            motor.direction = False
        else:
            # MOVE BACKWARD THEN FORWARD
            motor.direction = True
    
    def set_jog_parameters(self, servo_name):
        serial = self.open_motors[servo_name].serial
        self.check(self.dll.CC_RequestJogParams(serial))
        self.dll.CC_SetJogMode(serial, 1, 2)


class Motor:
    UM_PER_COUNT = 0.29
    BACKLASH = 6  # in µm. Maximum value for MTS50/M-Z8

    def __init__(self, serial):
        self.serial = serial
        self.direction = True  # direction is true if it is going forward, false otherwise

