from pyrpl import Pyrpl


class RedpitayaChannel(object):
    def __init__(self, pyrpl_instance):
        self.rp = pyrpl_instance.rp

    def in1(self):
        return self.rp.scope.voltage_in1

    def in2(self):
        return self.rp.scope.voltage_in2