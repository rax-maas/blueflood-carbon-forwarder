import sys

import twisted.internet
import protocols


def main():
    lineFactory = twisted.internet.protocol.ServerFactory()
    lineFactory.protocol = protocols.MetricLineReceiver

    pickleFactory = twisted.internet.protocol.ServerFactory()
    pickleFactory.protocol = protocols.MetricPickleReceiver

    twisted.internet.reactor.listenTCP(2003, lineFactory)
    twisted.internet.reactor.listenTCP(2004, pickleFactory)
    twisted.internet.reactor.run()
    return 0
    

if __name__ == '__main__':
    sys.exit(main())
