from trash.redpitaya_channel import RedpitayaChannel

class IonPumpPressure(RedpitayaChannel):
    def pressure(self):
       p = (350*self.in2()) * 10**(-3) / 10**2.6 #22* from 6dB attenuator
       #p = (( voltage* 10**(-3))/4.52)**(1/1.28)
       return p