import logging

from twisted.application.service import IServiceMaker, Service, MultiService
from twisted.internet.endpoints import serverFromString
from twisted.internet.protocol import Factory
from twisted.internet.task import LoopingCall
from twisted.application.internet import TCPServer
from twisted.plugin import IPlugin
from twisted.python import usage, log
from twisted.web.client import Agent
from zope.interface import implementer

from bluefloodserver.protocols import MetricLineReceiver, MetricPickleReceiver
from bluefloodserver.collect import MetricCollection, ConsumeFlush, BluefloodFlush
from bluefloodserver.blueflood import BluefloodEndpoint


class Options(usage.Options):
    DEFAULT_TTL = 60 * 60 * 24
    optParameters = [
        ['endpoint', 'e', 'tcp:2004', 'Twisted formatted endpoint to listen to pickle protocol metrics'],
        ['endpoint-plain', '', 'tcp:2003', 'Twisted formatted endpoint to listen to plain text protocol metrics'],
        ['interval', 'i', 30, 'Metric send interval, sec'],
        ['blueflood', 'b', 'http://localhost:19000', 'Blueflood server ingest URL (schema, host, port)'],
        ['tenant', 't', '', 'Blueflood tenant ID'],
        ['ttl', '', DEFAULT_TTL, 'TTL value for metrics, sec'],
        ['user', 'u', '', 'Rackspace authentication username. Leave empty if no auth is required'],
        ['pass', 'p', '', 'Rackspace authentication password']
    ]


class GraphiteMetricFactory(Factory):

    def __init__(self):
        flusher = ConsumeFlush()
        self._metric_collection = MetricCollection(flusher)

    def processMetric(self, metric, datapoint):
        log.msg('Receive metric {} {}:{}'.format(metric, datapoint[0], datapoint[1]), level=logging.DEBUG)
        self._metric_collection.collect(metric, datapoint)

    def flushMetric(self):
        try:
            log.msg('Sending {} metrics'.format(self._metric_collection.count()), level=logging.DEBUG)
            self._metric_collection.flush()
        except Exception, e:
            log.err(e)


class MetricService(Service):

    def __init__(self, protocol_cls, endpoint, interval, blueflood_url, tenant, ttl):
        self.protocol_cls = protocol_cls
        self.endpoint = endpoint
        self.flush_interval = interval
        self.blueflood_url = blueflood_url
        self.tenant = tenant
        self.ttl = ttl

    def startService(self):
        from twisted.internet import reactor

        server = serverFromString(reactor, self.endpoint)
        log.msg('Start listening at {}'.format(self.endpoint))
        factory = GraphiteMetricFactory.forProtocol(self.protocol_cls)
        self._setup_blueflood(factory, Agent(reactor))
        self.timer = LoopingCall(factory.flushMetric)
        self.timer.start(self.flush_interval)

        return server.listen(factory) 

    def stopService(self):
        self.timer.stop()

    def _setup_blueflood(self, factory, agent):
        log.msg('Send metrics to {} as {} with {} sec interval'
            .format(self.blueflood_url, self.tenant, self.flush_interval))
        client = BluefloodEndpoint(
            ingest_url=self.blueflood_url,
            tenant=self.tenant,
            agent=agent)
        flusher = BluefloodFlush(client=client, ttl=self.ttl)
        factory._metric_collection.flusher = flusher

@implementer(IServiceMaker, IPlugin)
class MetricServiceMaker(object):
    tapname = 'blueflood-forward'
    description = 'Forwarding metrics from graphite sources to Blueflood'
    options = Options

    def makeService(self, options):
        service = MultiService()

        MetricService(
            protocol_cls=MetricPickleReceiver,
            endpoint=options['endpoint'],
            interval=float(options['interval']),
            blueflood_url=options['blueflood'],
            tenant=options['tenant'],
            ttl=int(options['ttl'])
        ).setServiceParent(service)

        MetricService(
            protocol_cls=MetricLineReceiver,
            endpoint=options['endpoint-plain'],
            interval=float(options['interval']),
            blueflood_url=options['blueflood'],
            tenant=options['tenant'],
            ttl=int(options['ttl'])
        ).setServiceParent(service)

        return service


serviceMaker = MetricServiceMaker()