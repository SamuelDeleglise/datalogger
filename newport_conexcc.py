import sys

#add dlls to path
sys.path.append(r'C:/Newport/Motion Control/CONEX-CC/Bin')
import clr
clr.AddReference('Newport.CONEXCC.CommandInterface')
import CommandInterfaceConexCC
import time

DEV = 1                # hardcoded here to the first device


class ConexCC:
    MAX_VELOCITY = 0.4
    
    def __init__(self, com_port, velocity):
        self.min_limit = -1
        self.max_limit = -1
        self.cur_pos = -1
        self.controller_state = ''
        self.positioner_error = ''
        self.movement_sleep_time = 0.1
        self.done_moving_flag = '33'

        self.driver = CommandInterfaceConexCC.ConexCC()
        ret = self.driver.OpenInstrument(com_port)
        if ret != 0:
            print('Oops: error opening port %s' % com_port)
            self.positioner_error = 'init failed'
        else:
            print('ConexCC: Successfully connected to %s' % com_port)
            self.velocity
            self.velocity = velocity
            print('Velocity set to %.1f'%velocity)
            self.set_homing_velocity(velocity)
            self.read_limits()
            self.read_cur_pos()

    @classmethod
    def dump_possible_states(cls):
        # https://www.newport.com/mam/celum/celum_assets/resources/CONEX-CC_-_Controller_Documentation.pdf#page=54
        help_text = '''===== Conex-CC Controller States =====
            – 0A: NOT REFERENCED from RESET.
            – 0B: NOT REFERENCED from HOMING.
            – 0C: NOT REFERENCED from CONFIGURATION.
            – 0D: NOT REFERENCED from DISABLE.
            – 0E: NOT REFERENCED from READY.
            – 0F: NOT REFERENCED from MOVING.
            – 10: NOT REFERENCED - NO PARAMETERS IN MEMORY.
            – 14: CONFIGURATION.
            – 1E: HOMING.
            – 28: MOVING.
            – 32: READY from HOMING.
            – 33: READY from MOVING.
            – 34: READY from DISABLE.
            – 36: READY T from READY.
            – 37: READY T from TRACKING.
            – 38: READY T from DISABLE T.
            – 3C: DISABLE from READY.
            – 3D: DISABLE from MOVING.
            – 3E: DISABLE from TRACKING.
            – 3F: DISABLE from READY T.
            – 46: TRACKING from READY T.
            – 47: TRACKING from TRACKING.  
            ===========================================      
        '''
        for s in help_text.split('\n'):
            print(s.strip(' '))

    def read_limits(self):
        err_str = ''
        resp = 0
        res, resp, err_str = self.driver.SL_Get(DEV, resp, err_str)
        if res != 0 or err_str != '':
            print('Oops: Negative SW Limit: result=%d,response=%.2f,errString=\'%s\'' % (res, resp, err_str))
        else:
            print('Negative SW Limit = %.1f' % resp)
            self.min_limit = resp

        res, resp, err_str = self.driver.SR_Get(DEV, resp, err_str)
        if res != 0 or err_str != '':
            print('Oops: Positive SW Limit: result=%d,response=%.2f,errString=\'%s\'' % (res, resp, err_str))
        else:
            print('Positive SW Limit = %.1f' % resp)
            self.max_limit = resp

    def read_cur_pos(self):
        err_str = ''
        resp = 0
        res, resp, err_str = self.driver.TP(DEV, resp, err_str)
        if res != 0 or err_str != '':
            print('Oops: Current Position: result=%d,response=%.2f,errString=\'%s\'' % (res, resp, err_str))
        else:
            print('Current Position = %.3f' % resp)
            self.cur_pos = resp


    def exit_disable_state(self):
        err_str = ''
        state = 1  # enable
        res, err_str = self.driver.MM_Set(DEV, state, err_str)
        if res != 0 or err_str != '':
            print('Oops: Leave Disable: result=%d,errString=\'%s\'' % (res, err_str))
        else:
            print('Exiting DISABLE state')

    def init_positioner(self):
        err_str = ''
        res, err_str = self.driver.OR(DEV, err_str)
        if res != 0 or err_str != '':
            print('Oops: Find Home: result=%d,errString=\'%s\'' % (res, err_str))
        else:
            print('Finding Home')

    def set_homing_velocity(self, velocity):
        if velocity > self.MAX_VELOCITY:
            velocity = self.MAX_VELOCITY
        err_str = ''
        res, err_str = self.driver.OH_Set(DEV, velocity, err_str)
        if res != 0 or err_str != '':
            print('Oops: Homing velocity: result=%d,errString=\'%s\'' % (res, err_str))
        else:
            print('Homing velocity set to %.1f mm/s' % velocity)


    def move_relative_async(self, distance_um, verbose=False):
        '''
        The units of the distance is in microns. Moves the given distance from its original position
        '''
        if self.is_ready():
            err_str = ''
            res, err_str = self.driver.PR_Set(DEV, distance_um/1000, err_str)
            if res != 0 or err_str != '':
                print('Oops: Move Relative: result=%d,errString=\'%s\'' % (res, err_str))
            else:
                if verbose: print('Moving Relative %.3f um' % distance_um)
                
    def move_relative_sync(self, distance_um, timeout=30, n_retry=3, verbose=False):
        self.move_relative_async(distance_um, verbose=verbose)
        done = False
        time_start = time.time()
        while not done:
            if time.time() - time_start > timeout:
                raise ValueError("Timeout in move")
            time.sleep(self.movement_sleep_time)
            done = self.state==self.done_moving_flag
        # checks the movement is completely done (for fine movement endings can be the case)
    
    @property
    def velocity(self):
        err_str = ''
        resp = 0
        res, resp, err_str = self.driver.VA_Get(DEV, resp, err_str)
        if res != 0 or err_str != '':
            print('Oops: Current Velocity: result=%d,response=%.2f,errString=\'%s\'' % (res, resp, err_str))
        return resp
    
    @velocity.setter
    def velocity(self, v):
        if v > self.MAX_VELOCITY:
            v = self.MAX_VELOCITY
            print('Cannot set velocity higher than %.1f. Velocity set to maximal value'%v)
        err_str = ''
        res, err_str = self.driver.VA_Set(DEV, v, err_str)
        if res != 0 or err_str != '':
            print('Oops: Set velocity: result=%d,errString=\'%s\'' % (res, err_str))
        else:
            print('velocity Set to %.1f mm/s' % v)
    
    @property
    def state(self):
        err_str = ''
        resp = ''
        resp2 = ''
        res, resp, resp2, errString = self.driver.TS(DEV, resp, resp2, err_str)
        self._error = resp
        self._state = resp2
        return self._state
      
    @state.setter
    def state(self, resp):
        self._state =  resp
        
    @property
    def error(self):
        err_str = ''
        resp = ''
        resp2 = ''
        res, resp, resp2, errString = self.driver.TS(DEV, resp, resp2, err_str)
        self._error = resp
        self._state = resp2
        return self._error
      
    @error.setter
    def error(self, resp):
        self._error =  resp
          
     

    def close(self):
        # note that closing the communication will NOT stop the motor!
        self.driver.CloseInstrument()