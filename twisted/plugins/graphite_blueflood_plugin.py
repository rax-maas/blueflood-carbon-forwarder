from ConfigParser import ConfigParser

from twisted.application.service import IServiceMaker, Service
from twisted.internet.endpoints import serverFromString
from twisted.internet.protocol import Factory
from twisted.internet.task import LoopingCall
from twisted.application.internet import TCPServer
from twisted.plugin import IPlugin
from twisted.python import usage, log
from zope.interface import implementer

from bluefloodserver.protocols import MetricLineReceiver
from bluefloodserver.collect import MetricCollection, ConsumeFlush


class Options(usage.Options):
    optParameters = []


class GraphiteMetricFactory(Factory):

    def __init__(self):
        flusher = ConsumeFlush()
        self._metric_collection = MetricCollection(flusher)

    def processMetric(self, metric, datapoint):
        self._metric_collection.collect(metric, datapoint)

    def flushMetric(self):
        self._metric_collection.flush()


class MetricService(Service):

    def __init__(self, endpoint, interval):
        self._endpoint = endpoint
        self.flush_interval = interval

    def startService(self):
        from twisted.internet import reactor

        server = serverFromString(reactor, self._endpoint)
        factory = GraphiteMetricFactory.forProtocol(MetricLineReceiver)
        self.timer = LoopingCall(factory.flushMetric)
        self.timer.start(self.flush_interval)

        return server.listen(factory) 

    def stopService(self):
        self.timer.stop()

@implementer(IServiceMaker, IPlugin)
class MetricServiceMaker(object):
    tapname = 'blueflood-forward'
    description = 'Forwarding metrics from graphite sources to Blueflood'
    options = Options

    def makeService(self, options):
        config = ConfigParser()

        return MetricService(
            endpoint='tcp:2003',
            interval=5
        )


serviceMaker = MetricServiceMaker()