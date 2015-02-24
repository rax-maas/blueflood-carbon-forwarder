import time
import os

import mock

import bluefloodserver.collect as cl


def test_collect_and_flush():
    flusher = mock.MagicMock()
    collector = cl.MetricCollection(flusher)

    timestamp = time.time()
    metrics = []
    for i in range(10):
        metrics.append(('foo.bar.baz', i, timestamp))
        collector.collect('foo.bar.baz', (i, timestamp))
    collector.flush()

    assert flusher.flush.called_once_with(metrics)


def test_file_flish():
    file_name = 'output.txt'
    flusher = cl.FileFlush(file_name)
    collector = cl.MetricCollection(flusher)

    timestamp = time.time()
    for i in range(10):
        collector.collect('foo.bar.baz', (i, timestamp))
    collector.flush()

    file_data = open(file_name).read()
    os.remove(file_name)

    assert file_data == '\n'.join(
        ['foo.bar.baz {} {}'.format(i, timestamp) 
            for i in range(10)] + [''])

def test_blueflood_flush():
    client = mock.MagicMock()
    flusher = cl.BluefloodFlush(client)
    collector = cl.MetricCollection(flusher)

    timestamp = time.time()
    for i in range(10):
        collector.collect('foo.bar.baz', (i, timestamp))
    collector.flush()

    assert client.ingest.call_count == 10
    assert client.commit.called_once()