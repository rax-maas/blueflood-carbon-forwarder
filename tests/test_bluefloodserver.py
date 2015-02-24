import mock
import twisted.plugins.graphite_blueflood_plugin as plugin
from twisted.test import proto_helpers


def test_service():
    service = plugin.serviceMaker.makeService(plugin.Options())
    assert isinstance(service, plugin.MetricService)

def test_factory():
    factory = plugin.GraphiteMetricFactory()
    factory.protocol = plugin.MetricLineReceiver
    factory._metric_collection = mock.MagicMock()
    proto = factory.buildProtocol(('127.0.0.1', 0))
    tr = proto_helpers.StringTransport()
    proto.makeConnection(tr)

    proto.dataReceived('foo.bar.baz 123 123456789.0\n')
    assert factory._metric_collection.collect.called_once_with('foo.bar.baz', 123456789.0, 123.0)
    