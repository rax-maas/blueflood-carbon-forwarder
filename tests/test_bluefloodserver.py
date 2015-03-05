import StringIO
import json
import mock
import pytest
import twisted.plugins.graphite_blueflood_plugin as plugin
from twisted.web.client import Agent
from txKeystone import KeystoneAgent
from twisted.test import proto_helpers


def test_service():
    service = plugin.serviceMaker.makeService(plugin.Options())
    assert isinstance(service, plugin.MetricService)

def test_service_simple_agent():
    options = plugin.Options()
    service = plugin.serviceMaker.makeService(options)
    service._setup_blueflood = mock.MagicMock()
    service.startService()
    assert service._setup_blueflood.called
    assert isinstance(service._setup_blueflood.call_args_list[0][0][1], Agent)
    service.stopService()

def test_service_auth_agent():
    options = plugin.Options()
    options.parseOptions(['--user', 'user', '--key', 'key'])
    service = plugin.serviceMaker.makeService(options)
    service._setup_blueflood = mock.MagicMock()
    service.startService()
    assert service._setup_blueflood.called
    assert isinstance(service._setup_blueflood.call_args_list[0][0][1], KeystoneAgent)
    service.stopService()


def test_factory():
    factory = plugin.GraphiteMetricFactory()
    factory.protocol = plugin.MetricLineReceiver
    factory._metric_collection = mock.MagicMock()
    proto = factory.buildProtocol(('127.0.0.1', 0))
    tr = proto_helpers.StringTransport()
    proto.makeConnection(tr)

    proto.dataReceived('foo.bar.baz 123 123456789.0\n')
    assert factory._metric_collection.collect.called_once_with('foo.bar.baz', 123456789.0, 123.0)

def test_send_blueflood():
    factory = plugin.GraphiteMetricFactory()
    agent = mock.MagicMock()
    factory.protocol = plugin.MetricLineReceiver
    plugin.MetricService(
        protocol_cls=factory.protocol,
        endpoint='',
        interval=5,
        blueflood_url='http://bluefloodurl:190',
        tenant='tenant',
        ttl=30)._setup_blueflood(factory, agent)

    proto = factory.buildProtocol(('127.0.0.1', 0))
    tr = proto_helpers.StringTransport()
    proto.makeConnection(tr)

    proto.dataReceived('foo.bar.baz 123 123456789.0\n')
    factory.flushMetric()
    assert agent.request.called 
    assert len(agent.request.call_args_list) == 1
    rq = agent.request.call_args_list[0][0]
    assert rq[0] == 'POST'
    assert rq[1] == 'http://bluefloodurl:190/v2.0/tenant/ingest'
    metrics = json.loads(rq[3]._inputFile.read())
    assert len(metrics) == 1
    assert metrics[0]['metricName'] == 'foo.bar.baz'
    assert metrics[0]['metricValue'] == 123.0
