import os
import socket
import time

HOST = "127.0.0.1"
PORT = 52001

# Overridable from the environment so a capture session never has to edit this
# file:  PPS=200 LABEL=walk python3 packet_generator.py
#
# PPS is the ceiling on the receiver's CSI sampling rate — the RX can never log
# more rows/s than the TX sends packets/s, and it will log fewer once frame
# errors are counted. 200 leaves headroom above the ~50 Hz that activity
# recognition needs. See DATA_COLLECTION.md.
PPS = int(os.environ.get("PPS", 300))
PAYLOAD_SIZE = int(os.environ.get("PAYLOAD_SIZE", 100))
LABEL = os.environ.get("LABEL", "walking")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

print(f"Connected — sending {PPS} pkt/s, {PAYLOAD_SIZE}-byte payload, LABEL={LABEL}")

seq = 0

while True:
    timestamp = int(time.time() * 1000)

    msg = (
        f"SEQ={seq};"
        f"TS={timestamp};"
        f"LABEL={LABEL};"
    ).encode()

    payload = msg.ljust(PAYLOAD_SIZE, b'X')

    sock.sendall(payload)

    # One line per second rather than per packet — at 200 pps the old
    # per-packet print costs more time than the send does.
    if seq % PPS == 0:
        print(f"Sent {seq} packets ({PPS} pkt/s, LABEL={LABEL})")

    seq += 1

    time.sleep(1.0 / PPS)
