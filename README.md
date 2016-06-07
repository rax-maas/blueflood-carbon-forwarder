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
| --config | Set options from a config file | |

In case you need no authentication leave `-u`/`--user` command line argument empty (default value).
It is recommended not to set the `key` option from the command line, as that can compromise api keys. Instead, set the key in a config file and set the `--config` option to the name of the file.'


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

# Security Considerations
This tool makes use of Python's [`pickle`](https://docs.python.org/2/library/pickle.html) module to receive data from Graphite.
The `pickle` module is not intended to be secure against maliciously-constructed data.
In particular, specially-crafted payloads can be used to [execute arbitrary shell commands](https://blog.nelhage.com/2011/03/exploiting-pickle/) on the receiving side.
For this reason, the forwarder uses a `SafeUnpickler` to restrict what classes can be deserialized, at the cost of speed.
Normally, this shouldn't be a concern. However, if your application needs to deserialize objects at a faster rate, and the input is already known to be secure, the `get_unpickler` can made to return the default, insecure pickler.

# Failure Considerations

Errors in operation will naturally fall into two realms, input and output.
Errors on the inbound side will be related to the pickled data coming from carbon.
Errors on the outbound side will be unexpected (or missing or erroneous) HTTP responses from the blueflood instance to which the metrics are being sent.

## Accepting metrics in pickle format:

If a properly formatted pickle message is truncated during transmission, the metric won't be recorded, and no error or exception will be logged.

If a pickle message is not properly formatted (e.g. if `payload` gets truncated in `sendPickle.py` before `handle` is set), then the unpickler will raise `EOFError` and the exception will be written to the log.

## Forwarding metrics via HTTP:

The forwarder sends metrics to blueflood via an HTTP POST request to the `/v2.0/${tenant}/ingest` path.
For the most part, the response from that request is ignored. The response code _is_ checked, however.
If the response code is `200`, `201`, `202`, `204`, or `207`, the forwarder assumes that the request succeeded, and that the metrics were successfully ingested.
However, if the response code is anything else, then the behavior is a little more complex (see [Technical Details](#technical-details) below).
It is important to note that, if the response code is not one of the above (`200`, `201`, `202`, `204`, or `207`), then NO ERROR OR EXCEPTION IS LOGGED.
The response code received from the server _is_ logged, however.
If you want to know if there were any errors, you'll have to check the log.

There isn't any significant error handling logic in the code itself, but we can suggest some course of action based on the response code:

 - 207: Problematic. This is a multi-status response. The response body will contain the resultant responses of multiple operations aggregated into a single document. It's in the 2xx range, but that doesn't mean that all (or even any) of the combined operations succeeded. `BluefloodEndpoint` always treats `207` as a success, so if some metrics were rejected for some reason, it will _not_ try to resend them and they will be lost forever. This should probably be fixed in the forwarder, unless we can replace it with something else.
 - 401 or 403: Authentication failure. Double check the `tenant`, `key`, and `auth_url` config settings and try again.
 - 429: This response means that rate limits were exceeded. Usually, per-second or per-minute limits will have reset by the time the forwarder retries. If it continues to be a problem, settings the `interval` option to a larger number of seconds may help.
 - 5xx: This is a server-side error on blueflood's part. There are not any settings on the forwarder that can work around it.

## Technical Details:

There are two levels of "batching":
 - `MetricCollection._metrics`
 - `BluefloodEndpoint._json_buffer`

When the `interval` elapses, metric data will be moved from `_metrics` to `_json_buffer`.
Then, the `BluefloodEndpoint` will attempt to send the them to blueflood via HTTP.
If the HTTP request succeeds, then `_json_buffer` will be emptied.
If the request does not succeed, then the metrics will stay in the `Json_buffer` and be included in the next HTTP request.
The process is additionally complicated by the fact that the HTTP request is _only made if there is data in `metrics` waiting to be sent_.
If there is data in `_json_buffer` but not in `_metrics`, no attempt will be made to send them, and the data will just sit around in `_json_buffer`.
