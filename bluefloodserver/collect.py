class IFlush:

    def flush(self, metrics):
        raise('Not Implemented')

class ConsumeFlush(IFlush):

    def flush(self, metrics):
        pass

class FileFlush(IFlush):

    def __init__(self, filename):
        self.filename = filename

    def flush(self, metrics):
        with open(self.filename, 'a') as outfile:
            for name, time, value in metrics:
                outfile.write('{} {} {}\n'.format(name, time, value))


class BluefloodFlush(IFlush):

    def __init__(self, client, ttl=60*60*24):
        self.client = client
        self.ttl = ttl

    def flush(self, metrics):
        for name, time, value in metrics:
            self.client.ingest(name, time, value, self.ttl)
        self.client.commit()


class MetricCollection:        
    
    def __init__(self, flusher):
        self._metrics = []
        self.flusher = flusher

    def collect(self, metric, datapoint):
        self._metrics.append((metric, datapoint[0], datapoint[1]))

    def flush(self):
        if self._metrics:
            self.flusher.flush(self._metrics)
            self._metrics = []

    def count(self):
        return len(self._metrics)