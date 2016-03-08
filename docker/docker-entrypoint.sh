#!/bin/bash
: ${TENANT_ID="123"}
: ${LIMIT="1000000"}
: ${ENDPOINT="tcp:2004"}
: ${BLUEFLOOD_URL="localhost:19000"}
: ${METRIC_PREFIX=""}
: ${DEFAULT_TTL="86400"}
: ${METRICS_SEND_INTERVAL="30.0"}
: ${KEYSTONE_USER=""}
: ${KEYSTONE_KEY=""}
: ${AUTH_URL="https://identity.api.rackspacecloud.com/v2.0/tokens"}
if [[ -z "$METRIC_PREFIX" ]]
then
twistd --pidfile /var/run/twistd.pid --nodaemon --logger carbonforwarderlogging.forwarder_log_observer.get_log_observer blueflood-forward -e $ENDPOINT -b $BLUEFLOOD_URL -u $KEYSTONE_USER -k $KEYSTONE_KEY --auth_url $AUTH_URL --tenant $TENANT_ID --ttl $DEFAULT_TTL --limit=$LIMIT 
else
twistd --pidfile /var/run/twistd.pid --nodaemon --logger carbonforwarderlogging.forwarder_log_observer.get_log_observer blueflood-forward -e $ENDPOINT -b $BLUEFLOOD_URL -u $KEYSTONE_USER -k $KEYSTONE_KEY --auth_url $AUTH_URL --tenant $TENANT_ID -p $METRIC_PREFIX --ttl $DEFAULT_TTL --limit=$LIMIT
fi
