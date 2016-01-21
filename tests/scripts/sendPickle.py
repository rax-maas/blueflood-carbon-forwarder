'''
This is a simple test script that can be used to send pickle format 
metric to a twistd server running blueflood-forward. 
Modify the script as necessary for your testing need.
'''
import pickle
import socket
import struct
import time
import random

LISTEN_URL = ('localhost', 2004)
def send_to_socket(listOfMetricTuples):
    payload = pickle.dumps(listOfMetricTuples, protocol=2)
    header = struct.pack("!L", len(payload))
    message = header + payload
    print message
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(LISTEN_URL)
    sock.sendall(message)
    sock.close()

timestamp = int(time.time())
value = random.randint(100, 200)
name = 'my.metric.name.2'
send_to_socket([(name, (timestamp, value))])
