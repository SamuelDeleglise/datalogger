import requests
import numpy as np

class OpticReader(object):
    def __init__(self, ip='10.214.1.81'):
        self.ip = ip
        self.datas = []
        self.times = []


    def count(self):
        r = requests.get("http://"+self.ip+"/Python")
        data = r.content.split(';')
        count = float(data[0])
        t = float(data[1])
        self.datas.append(count)
        self.times.append(t)

        return count

    def time(self):
        r = requests.get("http://"+self.ip+"/Python")
        data = r.content.split(';')
        count = float(data[0])
        t = float(data[1])
        self.datas.append(count)
        self.times.append(t)
        return t

    def derivative(self):
        r = requests.get("http://" + self.ip + "/Python")
        data = r.content.split(';')
        count = float(data[0])
        t = float(data[1])
        if len(self.datas)>0:
            i=len(self.datas)-2
            dy = count-self.datas[len(self.datas)-1]
            dt = t-self.times[len(self.times)-1]
            while (dy == 0.) and (i>=0):
                dy = count - self.datas[i]
                dt = t - self.times[i]
                i=i-1
            self.datas.append(count)
            self.times.append(t)
            return 1000000.*dy/dt
        else:
            self.datas.append(count)
            self.times.append(t)
            return 0
