#!/usr/bin/env python

import os
import json
import pickle
import pytest
import SocketServer
import socket
import struct
import subprocess
import threading
import time
import urllib2

import http_server_mock

from twisted.internet import reactor, endpoints
from twisted.web import server


b_handler = None
a_handler = None
t = None


TENANT = 'tenant'
AUTH_URL = 'http://localhost:8001'
AUTH_USER = 'user1'
AUTH_KEY = 'key2'
BLUEFLOOD_URL = 'http://localhost:8000'
LISTEN_URL = ('localhost', 2004)
INTERVAL = 5
LIMIT = 1024 # 1 kilobyte

def run_twisted(user=None, key=None):
    args = ['twistd', '-n', '-l', 'log.txt', 'blueflood-forward',
     '-b', BLUEFLOOD_URL, '-i', str(INTERVAL), '-t', TENANT, '--limit', str(LIMIT)]
    if user:
        args.extend(['-u', user, '-k', key, '--auth_url', AUTH_URL])
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p

def send_to_socket(listOfMetricTuples):
    payload = pickle.dumps(listOfMetricTuples, protocol=2)
    header = struct.pack("!L", len(payload))
    message = header + payload
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(LISTEN_URL)
    sock.sendall(message)
    sock.close()

def setup_module(module):
    """ setup any state specific to the execution of the given module."""
    
    global b_handler, a_handler, t
    # blueflood server mock
    b_handler = http_server_mock.MockServerHandler()
    # auth server mock
    a_handler = http_server_mock.MockServerHandler()

    endpoints.serverFromString(reactor, "tcp:8000").listen(server.Site(b_handler))
    endpoints.serverFromString(reactor, "tcp:8001").listen(server.Site(a_handler))

    t = threading.Thread(target=reactor.run, args=(0, ))
    t.daemon = True
    t.start()

def teardown_module(module):
    """ teardown any state that was previously setup with a setup_module
    method.
    """
    global t

    reactor.stop()
    t = None


@pytest.fixture
def twistd(request):
    return fixture_run_twisted(request, None, None)

@pytest.fixture
def twistd_auth(request):
    return fixture_run_twisted(request, AUTH_USER, AUTH_KEY)
    
def fixture_run_twisted(request, user, key):
    p = run_twisted(user, key)
    def fin():
        p.terminate()
        print 'Waiting process to terminate'
        watchdog_timer = threading.Timer(5.0, p.kill, [p])
        watchdog_timer.start()
        p.wait()
        watchdog_timer.cancel()
        print 'quit', p, time.time()
        assert p.returncode == 0
    request.addfinalizer(fin)
    return p

def setup_and_teardown_handler(request, handler):
    cv = threading.Condition()
    handler.cv = cv
    def fin():
        handler.reset_to_default_reply()
        handler.cv = None
        handler.data = []
    request.addfinalizer(fin)
    return handler

@pytest.fixture
def blueflood_handler(request):
    global b_handler
    return setup_and_teardown_handler(request, b_handler)

@pytest.fixture
def auth_handler(request):
    global a_handler
    return setup_and_teardown_handler(request, a_handler)

def test_noauth(blueflood_handler, twistd):
    blueflood_handler.should_reply_forever(200, '', {})

    time.sleep(1.5)
    cv = blueflood_handler.cv
    timestamp = int(time.time())
    value = 10.0
    name = 'foo.bar.baz'
    send_to_socket([(name, (timestamp, value))])
    with cv:
        cv.wait(INTERVAL * 2)

    assert len(blueflood_handler.data) == 1
    _, headers, path, data = blueflood_handler.data[0]
    assert path == '/v2.0/tenant/ingest'
    metrics = json.loads(data)
    assert len(metrics) == 1
    assert metrics[0]['metricValue'] == value
    assert int(metrics[0]['collectionTime']/1000) == timestamp
    assert metrics[0]['metricName'] == name

def test_auth(blueflood_handler, auth_handler, twistd_auth):
    response = """{"access":{"token":{"id":"eb5e1d9287054898a55439137ea68675","expires":"2014-12-14T22:54:49.574Z","tenant":{"id":"836986","name":"836986"}}}}"""

    auth_handler.should_reply_forever(200, response, {})
    blueflood_handler.should_reply_once(200, '', {})
    time.sleep(1.0)

    timestamp = int(time.time())
    value = 10.0
    name = 'foo.bar.baz'
    send_to_socket([(name, (timestamp, value))])

    with auth_handler.cv:
        auth_handler.cv.wait(INTERVAL)
    assert len(auth_handler.data) == 1

    with blueflood_handler.cv:
        blueflood_handler.cv.wait(INTERVAL)
    assert len(blueflood_handler.data) == 1
    headers = blueflood_handler.data[0][1]
    assert 'x-auth-token' in headers
    assert headers['x-auth-token'] == 'eb5e1d9287054898a55439137ea68675'

def test_splitting_payload(blueflood_handler, twistd):
    blueflood_handler.should_reply_forever(200, '', {})
    cv = blueflood_handler.cv

    time.sleep(1.5)
    timestamp = int(time.time())
    value = 10.0
    name = 'foo.bar.baz'
    metrics = {
        'collectionTime': timestamp,
        'metricName': name,
        'metricValue': value,
        'ttlInSeconds': 86400
    }
    metric_size = len(json.dumps(metrics))
    count = LIMIT / metric_size + 1
    send_to_socket([(name, (timestamp, value)) for i in range(count)])
    with cv:
        cv.wait(INTERVAL * 2)

    assert len(blueflood_handler.data) > 1
    _, _, _, data = blueflood_handler.data[0]
    assert len(data) < LIMIT
    _, _, _, data_rest = blueflood_handler.data[1]
    assert len(data) != len(data_rest)