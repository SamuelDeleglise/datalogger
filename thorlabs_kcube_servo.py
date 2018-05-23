import ctypes as ct
import time
import math


class KCubeManager:
    DEVICE_MANAGER_DLL_PATH = "C:/Program Files/Thorlabs/Kinesis/Thorlabs.MotionControl.DeviceManager.dll"
    SERVO_DLL_PATH = "C:/Program Files/Thorlabs/Kinesis/Thorlabs.MotionControl.KCube.DCServo.dll"
    MOVEMENT_SLEEP_TIME = 0.02  # default seconds to wait for movement detection
    SIGNAL_WAIT_ATTEMPTS = 20  # default no of attempts to get the right signal

    def __init__(self):
        # Finds the dll
        self.device_manager_dll = ct.WinDLL(self.DEVICE_MANAGER_DLL_PATH)  # required to load self.dll
        self.dll = ct.WinDLL(self.SERVO_DLL_PATH)

        self.check(self.dll.TLI_BuildDeviceList())  # startup check
        self.device_no = self.dll.TLI_GetDeviceListSize()

        # Finds the connected serials
        self.ascii_serials = (ct.c_char*100)(100)
        self.check(self.dll.TLI_GetDeviceListByTypeExt(self.ascii_serials, 100, 27))
        self.ascii_serials = self.ascii_serials.value.decode('ascii')
        self.ascii_serials = self.ascii_serials.split(',')

        self.b_serials = []  # in binary format
        for i in range(self.device_no):
            self.b_serials.append(self.ascii_serials[i].encode())

        self.motors = dict()

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
        for name, motor in self.motors.items():
            if motor.serial == servo_serial:
                exists = 1
                found_name = name
                print('Serial {} already saved as {}'.format(servo_serial, found_name))
        if not exists:
            self.check(self.dll.CC_Open(servo_serial))
            self.motors[servo_name] = Motor(servo_serial, self.dll, self.MOVEMENT_SLEEP_TIME, self.SIGNAL_WAIT_ATTEMPTS)
            # self.set_jog_parameters(servo_name)

    def close(self, servo_name):
        """
        Closes the given servo motor
        :param servo_name:
        """
        self.dll.CC_Close(self.motors[servo_name].serial)  # not checked as True is returned, not an error code
        self.motors.pop(servo_name)

    def rename(self, old_name, new_name):
        """
        Rename the given servo motor
        :param old_name:
        :param new_name:
        """
        if old_name in self.motors.keys():
            motor = self.motors[old_name]
            self.motors.pop(old_name)
            self.motors[new_name] = motor
        else:
            print('{} is not a motor name. \nAvailable names are: {}'.format(old_name, self.motors.keys()))


class Motor:
    IS_MOVING_CLOCKWISE = 0x00000010
    IS_MOVING_COUNTERCLOCKWISE = 0x00000020
    IS_HOMING = 0x00000200
    IS_HOMED = 0x00000400
    UM_PER_COUNT = 0.29
    BACKLASH = 6  # in µm. Maximum value for MTS50/M-Z8

    def __init__(self, serial, dll, movement_sleep_time, signal_wait_attempts):
        self.serial = serial
        self.dll = dll
        self.movement_sleep_time = movement_sleep_time
        self.signal_wait_attempts = signal_wait_attempts

    @staticmethod
    def check(val):
        if val != 0:
            raise ValueError("Function returned error code %i" % val)

    @property
    def max_speed(self):
        """
        :return: ctype c_int
        """
        serial = self.serial
        self.check(self.dll.CC_RequestVelParams(serial))
        max_speed = ct.c_int()
        acceleration = ct.c_int()
        self.check(self.dll.CC_GetVelParams(serial, ct.byref(acceleration), ct.byref(max_speed)))
        return max_speed
    
    @max_speed.setter
    def max_speed(self, val):
        """
        Takes an int or a float (which is then forced to be int)
        :param val:
        """
        serial = self.serial
        self.check(self.dll.CC_RequestVelParams(serial))
        new_max_speed = ct.c_int(int(val))
        acceleration = self.acceleration
        self.check(self.dll.CC_SetVelParams(serial, acceleration, new_max_speed))

    @property
    def acceleration(self):
        """
        :return: ctype c_int
        """
        serial = self.serial
        self.check(self.dll.CC_RequestVelParams(serial))
        max_speed = ct.c_int()
        acceleration = ct.c_int()
        self.check(self.dll.CC_GetVelParams(serial, ct.byref(acceleration), ct.byref(max_speed)))
        return acceleration

    @acceleration.setter
    def acceleration(self, val):
        """
        Takes an int or a float (which is then forced to be int)
        :param val:
        """
        serial = self.serial
        self.check(self.dll.CC_RequestVelParams(serial))
        new_max_speed = self.max_speed
        acceleration = ct.c_int(int(val))
        self.check(self.dll.CC_SetVelParams(serial, acceleration, new_max_speed))

    def home_and_wait(self):
        """
        Homes the given servo, and waits for the movement to complete
        :param servo_name:
        :return: True if homing is seen to be completed, False if the homing is not found to start.
        """
        homing_started = self.act_and_wait_for_status_change(self.home, self.IS_HOMING)
        if homing_started:
            is_homing = True
            while is_homing:
                time.sleep(self.movement_sleep_time)
                is_homing = self.check_status(self.IS_HOMING)
            return True
        else:
            return False

    def move_relative_position_and_wait(self,  distance):
        """
        Moved the servo by the given distance. Can be positive or negative, in µm
        :param distance: in µm
        :return: True if movement is seen to be completed, False if the movement is not found to start.
        """
        if distance > 0:
            test = self.IS_MOVING_COUNTERCLOCKWISE
        else:
            test = self.IS_MOVING_CLOCKWISE
        movement_started = self.act_and_wait_for_status_change(self.move_relative_position, test, distance)
        if movement_started:
            is_moving = True
            while is_moving:
                time.sleep(self.movement_sleep_time)
                is_moving = self.check_status(test)
            return True
        else:
            return False

    def move_relative_position(self, *arg):
        """
        Moves forward (or backward) by the given distance (in µm) from current position
        :param arg: Should only be one single argument: the displacement (in µm)!
        Any other values will be ignored.
        """
        if len(arg) == 0:
            raise ValueError('Not enough arguments given')
        else:
            if len(arg) > 1:
                print('Too many arguments. Only the first kept')
            tick_pos = self.get_tick_position()
            while type(arg) is tuple:
                arg = arg[0]  # to ensure only first arg is kept
            tick_jog = int(arg/self.UM_PER_COUNT)
            self.move_to_position(tick_pos+tick_jog)

    def home(self):
        self.check(self.dll.CC_Home(self.serial))

    def move_to_position(self, *arg):
        """
        Moves to a given position (in device units)
        :param arg: Should only be one single argument: the position (in servo ticks)!
        Any other values will be ignored.
        """
        if len(arg) == 0:
            raise ValueError('Not enough arguments given')
        else:
            if len(arg) > 1:
                print('Too many arguments. Only the first kept')
            self.check(self.dll.CC_MoveToPosition(self.serial, arg[0]))

    def check_status(self, status_to_check):
        serial = self.serial
        self.check(self.dll.CC_RequestStatusBits(serial))
        try:
            res = self.dll.CC_GetStatusBits(serial)
            res_bin = self.signed_bin(res)
            res_bin = res_bin[::-1]
        except TypeError as e:
            raise KCubeResponseError(e+'\nCheck if motor is overloaded.')

        index_to_check = int(math.log(status_to_check, 2))
        status = bool(int(res_bin[index_to_check]))
        return status

    def check_homing_need(self):
        """
        :return: Returns True if the device needs to be homed before moving, False otherwise
        """
        serial = self.serial
        return not bool(self.dll.CC_CanMoveWithoutHomingFirst(serial))

    def act_and_wait_for_status_change(self, act_func, status_to_check, *func_args):
        """
        Await a (relatively) immediate response to a given action. Will fail for long steps is SIGNAL_WAIT_ATTEMPTS
        is small.
        :param act_func: the function to act, and whose result to await
        :param status_to_check:
        :param func_args: arguments used for the act_func. servo_name IS NOT counted amongst them
        :return: True is status change detected, False otherwise
        """
        old_status = self.check_status(status_to_check)
        if len(func_args) > 0:
            act_func(func_args)
        else:
            act_func()
        time.sleep(self.movement_sleep_time)
        for i in range(self.signal_wait_attempts):
            new_status = self.check_status(status_to_check)
            if new_status == old_status:
                time.sleep(self.movement_sleep_time)
            else:
                return True
            if i == (self.signal_wait_attempts-1):
                return False

    def get_tick_position(self):
        serial = self.serial
        self.check(self.dll.CC_RequestPosition(serial))
        tick_pos = self.dll.CC_GetPosition(serial)
        return tick_pos

    def get_position(self):
        # in µm
        tick_pos = self.get_tick_position()
        pos = tick_pos * self.UM_PER_COUNT
        return pos
    """
    def set_jog_parameters(self, servo_name):
        serial = self.motors[servo_name].serial
        self.check(self.dll.CC_RequestJogParams(serial))
        self.dll.CC_SetJogMode(serial, 1, 2)

    def set_move_velocity(self):
        serial = self.serial
        self.check(self.dll.CC_RequestJogParams(serial))
        self.dll.CC_SetJogMode(serial, 1, 2)
    """

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


class KCubeResponseError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
