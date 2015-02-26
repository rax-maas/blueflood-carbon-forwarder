# Description

Graphite _'backend'_. Twisted-based server accepts graphite source metrics and forward them to [blueflood][blueflood-git].

Server accepts both plain text and pickle protocols metrics. (Pickle protocol is still under development).

It does very primitive _'caching'_: aggregates all metrics and flushes them in regular intervals.

# Dependencies

 * twisted
 * mock
 * pytest

# Installation

    git clone https://github.com/rampage644/graphite-http-wrapper
    cd graphite-http-wrapper
    python setup.py install

# Running

    twistd blueflood-forward

# Configuration

Configuration is done with command line arguments passed to twistd daemon when running:

    twistd -n -l - blueflood-forward --help

| Switch | Description | default |
| - | - | - |
| -e | Endpoint to listen on | tcp:2003|
| -i | Metrics send interval, sec | 30.0 |
| -b | Blueflood address | http://localhost:19000 |
| -t | Tenand ID | tenant |
| --ttl | TimeToLive value for metrics, sec | 86400 |