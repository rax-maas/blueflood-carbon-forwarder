import os

from twisted.logger import FilteringLogObserver, LogLevelFilterPredicate, LogLevel, jsonFileLogObserver
from twisted.python import logfile

log_dir = os.environ.get("LOG_DIR", '/var/log/')
log_level = os.environ.get("TWISTED_LOG_LEVEL", 'INFO').lower()
log_rotate_length = os.environ.get("LOG_ROTATE_LENGTH", 100000)
max_rotated_log_files = os.environ.get("MAX_LOG_ROTATED_FILES", 100)

def get_log_observer():
    f = logfile.LogFile("carbon_forwarder.log", log_dir, rotateLength=log_rotate_length, maxRotatedFiles=max_rotated_log_files)
    observer = jsonFileLogObserver(f)
    filterer = FilteringLogObserver(observer,
        [LogLevelFilterPredicate(
            LogLevel.levelWithName(log_level))])
    return filterer
