import requests

class MagneticReader(object):

    def __init__(self, ip='10.214.1.91'):
        self.ip = ip
        #self.counts = []
        #self.flows = []

    def count_flow(self):
        r = requests.get("http://" + self.ip + "/Python")
        count = float(r.text.split('is')[1].rstrip('and actual flow'))
        flow = float(r.text.split('is')[2].rstrip())
        #self.counts.append(count)
        #self.flows.append(flow)

        return count, flow

    def count(self):
        return self.count_flow()[0]

    def flow(self):
        return self.count_flow()[1]

    def count_mod_1000(self):
        return self.count()%1000



    #
    # def flow(self):
    #     r = requests.get("http://" + self.ip + "/Python")
    #     count = int(r.text.split('is')[1].rstrip('and actual flow'))
    #     flow = float(r.text.split('is')[2].rstrip())
    #     self.counts.append(count)
    #     self.flows.append(flow)
    #
    #     return count

