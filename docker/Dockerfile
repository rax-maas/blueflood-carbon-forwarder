FROM python:2.7

MAINTAINER gaurav.bajaj@rackspace.com

RUN pip install service_identity
RUN pip install blueflood-carbon-forwarder
ADD docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
EXPOSE 2007
