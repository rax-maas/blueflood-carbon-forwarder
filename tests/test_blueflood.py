#!/usr/bin/env python
import urllib2
import time
import json 
import pytest

from twisted.web.client import Agent, FileBodyProducer, readBody
from bluefloodserver.blueflood import BluefloodEndpoint


try:
    b = BluefloodEndpoint()
    b.ingest('f.b.z', 1, 1, 1)
    b.commit()
except urllib2.URLError, e:
    skip = True
else:
    skip = False

@pytest.fixture
def setup():
    return BluefloodEndpoint()

@pytest.inlineCallbacks
@pytest.mark.skipif(skip, reason="Blueflood isn't running")
def testSingleIngest(setup):
    endpoint = setup
    name = 'example.metric.single.ingest'
    ttl = 10
    endpoint.ingest(name, 1376509892612, 50, ttl) 
    d = yield endpoint.commit()
    assert d.code == 200

@pytest.inlineCallbacks
@pytest.mark.skipif(skip, reason="Blueflood isn't running")
def testListIngest(setup):
    endpoint = setup
    name = 'example.metric.list.ingest'
    ttl = 10
    endpoint.ingest(name,
                    [1376509892612, 1376509892613, 1376509892614], 
                    [50, 51, 52], 
                    ttl)
    d = yield endpoint.commit()
    assert d.code == 200
    with pytest.raises(Exception):
        endpoint.ingest(name, 
                        [1376509892612, 1376509892613, 1376509892614], 
                        50, 
                        ttl)

@pytest.inlineCallbacks
@pytest.mark.skipif(skip, reason="Blueflood isn't running")
def testMultipleIngest(setup):
    endpoint = setup
    name = 'example.metric.multiple.ingest'
    ttl = 10
    times, values = list(range(5)), [50.0] * 5
    for t, v in zip(times, values):
         endpoint.ingest(name, t, v, ttl)
    d = yield endpoint.commit()
    assert d.code == 200
    resp = yield endpoint.retrieve_resolution(name, 0, 10)
    data = yield readBody(resp)
    assert len(json.loads(data)['values']) == 5

@pytest.inlineCallbacks
@pytest.mark.skipif(skip, reason="Blueflood isn't running")
def testRetrieveByResolution(setup):
    endpoint = setup
    name = 'example.metric.retrieve'
    ttl = 10
    timestamp = int(time.time())
    value = 50
    # insert first
    endpoint.ingest(name, timestamp, value, ttl)
    d = yield endpoint.commit()
    assert d.code == 200
    # range is 0-time
    resp = yield endpoint.retrieve_resolution(name, 0, timestamp + 10)
    rdata = yield readBody(resp)
    data = json.loads(rdata)
    assert len(data) != 0
    assert len(data['values']) != 0
    assert data['values'][0]['numPoints'] == 1
    assert data['values'][0]['average'] == value

@pytest.inlineCallbacks
@pytest.mark.skipif(skip, reason="Blueflood isn't running")
def testRetrieveByPoints(setup):
    endpoint = setup
    name = 'example.metric.retrieve'
    ttl = 10
    timestamp = int(time.time())
    value = 50
    # insert first
    endpoint.ingest(name, timestamp, value, ttl)
    d = yield endpoint.commit()
    assert d.code == 200
    # range is 0-time
    resp = yield endpoint.retrieve_points(name, 0, timestamp + 10, 200)
    rdata = yield readBody(resp)
    data = json.loads(rdata)
    assert len(data) != 0
    assert len(data['values']) != 0
    assert data['values'][0]['numPoints'] == 1
    assert data['values'][0]['average'] == value


if __name__ == '__main__':
    pytest.main()
