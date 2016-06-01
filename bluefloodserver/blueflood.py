#!/usr/bin/env python

import urllib2
import urlparse
import json
import logging

from StringIO import StringIO

from twisted.internet import reactor
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, FileBodyProducer, readBody
from twisted.web.http_headers import Headers
from twisted.python import log

def _get_metrics_url(url, tenantId):
    return url + '/v2.0/'\
        + tenantId + '/ingest'

def _get_metrics_query_url(url, tenantId,
                           metricName, start, end, points):
    return url + '/v2.0/' + tenantId\
        + '/views/' + metricName\
        + '?from=' + str(start) + '&to=' + str(end) + '&points=' + str(points)

def _get_metrics_query_url_resolution(url, tenantId,
                           metricName, start, end, resolution='FULL'):
    return url + '/v2.0/' + tenantId\
        + '/views/' + metricName\
        + '?from=' + str(start) + '&to=' + str(end) + '&resolution=' + resolution


class LimitExceededException(Exception):
    pass


class BluefloodEndpoint():

    def __init__(self, ingest_url='http://localhost:19000', retrieve_url='http://localhost:20000', tenant='tenant-id', agent=None, limit=None):
        self.agent = agent
        self.ingest_url = ingest_url
        self.retrieve_url = retrieve_url
        self.tenant = tenant
        self._json_buffer = []
        self.headers = {}
        self.limit = limit
        self._buffer_size = 0

    def ingest(self, metric_name, time, value, ttl):
        if not isinstance(time, list):
            time = [time]
        if not isinstance(value, list):
            value = [value]
        if len(time) != len(value):
            raise Exception('time and value list lengths differ')


        data = [{
            "collectionTime": t*1000,
            "ttlInSeconds": ttl,
            "metricValue": v,
            "metricName": metric_name
        } for t,v in zip(time, value)]
        row_size = len(json.dumps(data))
        # len('[]'') = 2, len(',' * total) = len(data) - 1
        if self.limit and row_size + len(self._json_buffer) - 1 + self._buffer_size > self.limit:
            raise LimitExceededException('JSON limit exceeded. Commit metrics before next ingest')
        self._json_buffer.extend(data)
        self._buffer_size += row_size

    @inlineCallbacks
    def commit(self):
        body = FileBodyProducer(StringIO(json.dumps(self._json_buffer)))
        url = _get_metrics_url(self.ingest_url, self.tenant)
        d = self.agent.request(
            'POST',
            url,
            Headers(self.headers),
            body)

        resp = yield d
        log.msg('POST {}, resp_code={}'.format(url, resp.code), level=logging.DEBUG)
        if resp.code in [200,201,202,204,207]:
            self._json_buffer = []
            self._buffer_size = 0
        returnValue(None)


    @inlineCallbacks
    def retrieve_points(self, metric_name, start, to, points):
        d = self.agent.request(
            'GET',
            _get_metrics_query_url(self.retrieve_url,
                self.tenant, metric_name, start, to, points),
            Headers(self.headers),
            None)
        resp = yield d
        body = yield readBody(resp)

        returnValue(json.loads(body))

    retrieve = retrieve_points

    @inlineCallbacks
    def retrieve_resolution(self, metric_name, start, to, resolution='FULL'):
        d = self.agent.request(
            'GET',
            _get_metrics_query_url_resolution(self.retrieve_url,
                self.tenant, metric_name, start, to, resolution),
            Headers(self.headers),
            None)

        resp = yield d
        body = yield readBody(resp)

        returnValue(json.loads(body))
