import socket
import time

HOST = "127.0.0.1"
PORT = 52001

PPS = 50
PAYLOAD_SIZE = 500
LABEL = "walking"

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

print("Connected")

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

    print(f"Sent packet {seq}")

    seq += 1

    time.sleep(1.0 / PPS)
