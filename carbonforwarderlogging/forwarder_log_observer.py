import os

from twisted.logger import FilteringLogObserver, LogLevelFilterPredicate, LogLevel, jsonFileLogObserver
from twisted.python import logfile
from twisted.python.log import FileLogObserver

log_dir = os.environ.get("LOG_DIR", '/var/log/')
log_level = os.environ.get("TWISTED_LOG_LEVEL", 'INFO').lower()
log_rotate_length = int(os.environ.get("LOG_ROTATE_LENGTH", 100000000))
max_rotated_log_files = int(os.environ.get("MAX_LOG_ROTATED_FILES", 10))

def get_log_observer():
    f = logfile.LogFile("carbon_forwarder.log", log_dir, rotateLength=log_rotate_length, maxRotatedFiles=max_rotated_log_files)
    observer = FileLogObserver(f)
    filterer = FilteringLogObserver(observer.emit,
        [LogLevelFilterPredicate(
            LogLevel.levelWithName(log_level))])
    return filterer

def get_json_log_observer():
    f = logfile.LogFile("carbon_forwarder.log", log_dir, rotateLength=log_rotate_length, maxRotatedFiles=max_rotated_log_files)
    observer = jsonFileLogObserver(f)
    filterer = FilteringLogObserver(observer,
        [LogLevelFilterPredicate(
            LogLevel.levelWithName(log_level))])
    return filterer
