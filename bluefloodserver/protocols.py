import time

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
from twisted.internet.error import ConnectionDone
from twisted.protocols.basic import LineOnlyReceiver, Int32StringReceiver

import util


class MetricReceiver:

    def connectionMade(self):
      pass

    def metricReceived(self, metric, datapoint):
        if datapoint[1] != datapoint[1]:
            return
        if int(datapoint[0]) == -1:
            datapoint = (time.time(), datapoint[1])

        self.factory.processMetric(metric, datapoint)

class MetricLineReceiver(MetricReceiver, LineOnlyReceiver):
    delimiter = '\n'

    def lineReceived(self, line):
        try:
            metric, value, timestamp = line.strip().split()
            datapoint = (float(timestamp), float(value))
        except ValueError:
            return

        self.metricReceived(metric, datapoint)


class MetricDatagramReceiver(MetricReceiver, DatagramProtocol):

    def datagramReceived(self, data, (host, port)):
        for line in data.splitlines():
            try:
                metric, value, timestamp = line.strip().split()
                datapoint = (float(timestamp), float(value))

                self.metricReceived(metric, datapoint)
            except ValueError:
                pass


class MetricPickleReceiver(MetricReceiver, Int32StringReceiver):
    MAX_LENGTH = 2 ** 20

    def connectionMade(self):
        MetricReceiver.connectionMade(self)
        self.unpickler = util.get_unpickler(
            insecure=True)

    def stringReceived(self, data):
        try:
            datapoints = self.unpickler.loads(data)
        except util.pickle.UnpicklingError:
            return

        for (metric, datapoint) in datapoints:
            try:
                datapoint = (float(datapoint[0]), float(datapoint[1]))
            except ValueError:
                continue

            self.metricReceived(metric, datapoint)
