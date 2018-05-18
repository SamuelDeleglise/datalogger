import ctypes as ct
import time
import math


class KCubeManager:
    DEVICE_MANAGER_DLL_PATH = "C:/Program Files/Thorlabs/Kinesis/Thorlabs.MotionControl.DeviceManager.dll"
    SERVO_DLL_PATH = "C:/Program Files/Thorlabs/Kinesis/Thorlabs.MotionControl.KCube.DCServo.dll"
    MOVEMENT_SLEEP_TIME = 0.02  # seconds to wait for movement detection
    IS_MOVING_CLOCKWISE = 0x00000010
    IS_MOVING_COUNTERCLOCKWISE = 0x00000020
    IS_HOMING = 0x00000200
    IS_HOMED = 0x00000400
    SIGNAL_WAIT_ATTEMPTS = 20

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
            raise ValueError("Function returned error code %i" % val)

    def connect(self, servo_serial, servo_name='MyServos'):
        """
        Connects to the given servo motor (by serial), and assigning it a name
        :param servo_serial:
        :param servo_name:
        """
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
        """
        Closes the given servo motor
        :param servo_name:
        """
        self.dll.CC_Close(self.open_motors[servo_name].serial)  # not checked as True is returned, not an error code
        self.open_motors.pop(servo_name)

    def rename(self, old_name, new_name):
        """
        Rename the given servo motor
        :param old_name:
        :param new_name:
        """
        if old_name in self.open_motors.keys():
            serial = self.open_motors[old_name].serial
            self.open_motors.pop(old_name)
            self.open_motors[new_name] = Motor(serial)
        else:
            print('{} is not a motor name. \nAvailable names are: {}'.format(old_name, self.open_motors.keys()))

    def home_and_wait(self, servo_name):
        """
        Homes the given servo, and waits for the movement to complete
        :param servo_name:
        :return: True if homing is seen to be completed, False if the homing is not found to start.
        """
        homing_started = self.act_and_wait_for_status_change(servo_name, self.home, self.IS_HOMING)
        if homing_started:
            is_homing = True
            while is_homing:
                time.sleep(self.MOVEMENT_SLEEP_TIME)
                is_homing = self.check_status(servo_name, self.IS_HOMING)
            return True
        else:
            return False

    def more_relative_position_and_wait(self, servo_name, distance):
        """
        Moved the servo by the given distance. Can be positive or negative, in µm
        :param servo_name:
        :param distance: in µm
        :return: True if movement is seen to be completed, False if the movement is not found to start.
        """
        if distance > 0:
            test = self.IS_MOVING_COUNTERCLOCKWISE
        else:
            test = self.IS_MOVING_CLOCKWISE
        movement_started = self.act_and_wait_for_status_change(servo_name, self.move_relative_position, test, distance)
        if movement_started:
            is_moving = True
            while is_moving:
                time.sleep(self.MOVEMENT_SLEEP_TIME)
                is_moving = self.check_status(servo_name, test)
            return True
        else:
            return False

    def move_relative_position(self, servo_name, *arg):
        """
        Moves forward (or backward) by the given distance (in µm) from current position
        :param servo_name:
        :param arg: Should only be one single argument: the displacement (in µm)!
        Any other values will be ignored.
        """
        if len(arg) == 0:
            raise ValueError('Not enough arguments given')
        else:
            if len(arg) > 1:
                print('Too many arguments. Only the first kept')
            tick_pos = self.get_tick_position(servo_name)
            arg = arg[0]  # to flatten any additional levels from the check_status function
            tick_jog = int(arg[0]/self.open_motors[servo_name].UM_PER_COUNT)
            self.move_to_position(servo_name, tick_pos+tick_jog)

    def home(self, servo_name):
        self.check(self.dll.CC_Home(self.open_motors[servo_name].serial))

    def move_to_position(self, servo_name, *arg):
        """
        Moves to a given position (in device units)
        :param servo_name:
        :param arg: Should only be one single argument: the position (in servo ticks)!
        Any other values will be ignored.
        """
        if len(arg) == 0:
            raise ValueError('Not enough arguments given')
        else:
            if len(arg) > 1:
                print('Too many arguments. Only the first kept')
            self.check(self.dll.CC_MoveToPosition(self.open_motors[servo_name].serial, arg[0]))

    def check_status(self, servo_name, status_to_check):
        serial = self.open_motors[servo_name].serial
        self.check(self.dll.CC_RequestStatusBits(serial))
        res = self.dll.CC_GetStatusBits(serial)
        res_bin = self.signed_bin(res)
        res_bin = res_bin[::-1]
        index_to_check = int(math.log(status_to_check, 2))
        status = bool(int(res_bin[index_to_check]))
        return status

    def check_homing_need(self, servo_name):
        """
        :param servo_name:
        :return: Returns True if the device needs to be homed before moving, False otherwise
        """
        serial = self.open_motors[servo_name].serial
        return not bool(self.dll.CC_CanMoveWithoutHomingFirst(serial))

    def act_and_wait_for_status_change(self, servo_name, act_func, status_to_check, *func_args):
        """
        Await a (relatively) immediate response to a given action.
        :param servo_name:
        :param act_func: the function to act, and whose result to await
        :param status_to_check:
        :param func_args: arguments used for the act_func. servo_name IS NOT counted amongst them
        :return: True is status change detected, False otherwise
        """
        old_status = self.check_status(servo_name, status_to_check)
        if len(func_args) > 0:
            act_func(servo_name, func_args)
        else:
            act_func(servo_name)
        time.sleep(self.MOVEMENT_SLEEP_TIME)
        for i in range(self.SIGNAL_WAIT_ATTEMPTS):
            new_status = self.check_status(servo_name, status_to_check)
            if new_status == old_status:
                time.sleep(self.MOVEMENT_SLEEP_TIME)
            else:
                return True
            if i == (self.SIGNAL_WAIT_ATTEMPTS-1):
                return False

    def get_tick_position(self, servo_name):
        serial = self.open_motors[servo_name].serial
        self.check(self.dll.CC_RequestPosition(serial))
        tick_pos = self.dll.CC_GetPosition(serial)
        return tick_pos

    def get_position(self, servo_name):
        # in µm
        tick_pos = self.get_tick_position(servo_name)
        pos = tick_pos * self.open_motors[servo_name].UM_PER_COUNT
        return pos

    def set_jog_parameters(self, servo_name):
        serial = self.open_motors[servo_name].serial
        self.check(self.dll.CC_RequestJogParams(serial))
        self.dll.CC_SetJogMode(serial, 1, 2)

    @staticmethod
    def twos_complement(old_bin):
        """
        Takes a binary number in string format (e.g. '00110'), and changes the 0s to 1s and vice_vera
        """
        new_bin = ''
        for no in old_bin:
            new_bin = new_bin + str((int(no)+1) % 2)
        return new_bin

    def signed_bin(self, val):
        """
        Converts a given signed decimal number into binary
        :param val:
        :return: bin_val
        """
        if val < 0:
            binary = '{:032b}'.format(val)
            new_bin = '1'  # sign indicator
            bin_val = binary[1:]
            new_bin = new_bin + self.twos_complement(bin_val)
        else:
            new_bin = val
        return new_bin


class Motor:
    UM_PER_COUNT = 0.29
    BACKLASH = 6  # in µm. Maximum value for MTS50/M-Z8

    def __init__(self, serial):
        self.serial = serial

