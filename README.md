# Description

Graphite _'backend'_. Twisted-based server accepts graphite source metrics and forward them to [blueflood][blueflood-git].

Server accepts only pickle protocols metrics (as it's the only protocol used by graphite `carbon-relay`.)

It does very primitive _'caching'_: aggregates all metrics and flushes them in regular intervals.

# Dependencies

 * twisted
 * mock
 * pytest
 * txKeystone

# Installation

```
    git clone https://github.com/rackerlabs/blueflood-carbon-forwarder.git
    cd blueflood-carbon-forwarder
    python setup.py install
```

# Running

```
    twistd blueflood-forward
```
| Switch | Description | default |
| ----- | ------- | --------- |
| -e | Endpoint to listen on for pickle protocol metrics | tcp:2004 |
| -i | Metrics send interval, sec | 30.0 |
| -b | Blueflood address | http://localhost:19000 |
| -t | Tenant ID | tenant |
| -p | Prefix to be prepended to metrics name | metric_prefix |
| --ttl | TimeToLive value for metrics, sec | 86400 |
| -u | Keystone user | |
| -k | Keystone key | |
| --auth-url | Keystone token URL | |

In case you need no authentication leave `-u`/`--user` command line argument empty (default value).


# Sending metrics

To send a test metric to the twistd server you started above, you can run the following:
```
    python tests/scripts/sendPickle.py
```
Modify the script accordingly for your local testing

# Configuration

Configuration is done with command line arguments passed to twistd daemon when running:
```
    twistd -n -l - blueflood-forward --help

```

#Logging 

Logging can be controlled using LogObserver provided along or you can use your own LogObserver

```
    twistd --logger carbonforwarderlogging.forwarder_log_observer.get_log_observer blueflood-forward
```
 
[blueflood-git]: https://github.com/rackerlabs/blueflood "blueflood"

# Running unit tests
```
pip install -r requirements.txt
py.test
```

