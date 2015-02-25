#!/usr/bin/env python

import urllib2
import urlparse
import json


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


class BluefloodEndpoint():

    def __init__(self, ingest_url='http://localhost:19000', retrieve_url='http://localhost:20000', tenant='tenant-id'):
        self.ingest_url = ingest_url
        self.retrieve_url = retrieve_url
        self.tenant = tenant
        self._json_buffer = []
        self.headers = {}

    def ingest(self, metric_name, time, value, ttl):
        if not isinstance(time, list):
            time = [time]
        if not isinstance(value, list):
            value = [value]
        if len(time) != len(value):
            raise Exception('time and value list lengths differ')


        data = [{
            "collectionTime": t,
            "ttlInSeconds": ttl,
            "metricValue": v,
            "metricName": metric_name
        } for t,v in zip(time, value)]
        self._json_buffer.extend(data)

    def commit(self):
        req = urllib2.Request(_get_metrics_url(self.ingest_url, self.tenant),
            json.dumps(self._json_buffer), self.headers)
        r = urllib2.urlopen(req)
        self._json_buffer = []
        return r.read()


    def retrieve_points(self, metric_name, start, to, points):
        req = urllib2.Request(_get_metrics_query_url(self.retrieve_url, self.tenant,
            metric_name, start, to, points), None, self.headers)
        r = urllib2.urlopen(req)
        response = r.read()
        return json.loads(response)

    retrieve = retrieve_points

    def retrieve_resolution(self, metric_name, start, to, resolution='FULL'):
        req = urllib2.Request(_get_metrics_query_url_resolution(self.retrieve_url, self.tenant,
            metric_name, start, to, resolution), None, self.headers)
        r = urllib2.urlopen(req)
        response = r.read()
        return json.loads(response)
