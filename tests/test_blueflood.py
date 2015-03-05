#!/usr/bin/env python
import urllib2
import time
import json 
import pytest

from twisted.web.client import Agent, FileBodyProducer, readBody
from twisted.internet import reactor
from bluefloodserver.blueflood import BluefloodEndpoint


try:
    b = BluefloodEndpoint()
    data = urllib2.urlopen(b.ingest_url).read()
except urllib2.HTTPError, e:
    skip = False
except urllib2.URLError, e:
    skip = True
else:
    skip = False

@pytest.fixture
def setup():
    return BluefloodEndpoint(agent=Agent(reactor))

@pytest.inlineCallbacks
@pytest.mark.skipif(skip, reason="Blueflood isn't running")
def testSingleIngest(setup):
    endpoint = setup
    name = 'example.metric.single.ingest'
    ttl = 10
    endpoint.ingest(name, 1376509892612, 50, ttl) 
    yield endpoint.commit()

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
    yield endpoint.commit()
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
    yield endpoint.commit()
    data = yield endpoint.retrieve_resolution(name, 0, 10)
    assert len(data['values']) == 5

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
    yield endpoint.commit()
    # range is 0-time
    data = yield endpoint.retrieve_resolution(name, 0, timestamp + 10)
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
    timestamp = 1234567
    value = 50
    # insert first
    endpoint.ingest(name, timestamp, value, ttl)
    yield endpoint.commit()
    # range is 0-time
    data = yield endpoint.retrieve_points(name, 0, timestamp, 200)
    assert len(data) != 0
    assert len(data['values']) != 0
    assert data['values'][0]['numPoints'] == 1
    assert data['values'][0]['average'] == value

@pytest.inlineCallbacks
def testNoConnection():
    endpoint = BluefloodEndpoint(ingest_url='http://localhost:9623',
        retrieve_url='http://localhost:8231')
    with pytest.raises(Exception):
        d = yield endpoint.commit()
    with pytest.raises(Exception):
        yield endpoint.retrieve_points('', 0, 0, 0)
    with pytest.raises(Exception):
        yield endpoint.retrieve_resolution('', 0, 0)


if __name__ == '__main__':
    pytest.main()
