import re

with open('wifi_rx.py', 'r') as f:
    content = f.read()

# Remove zeromq push sink instantiation
content = re.sub(r'self\.zeromq_push_sink_0.*?\n', '', content)

# Remove the connection involving extract_csi_0 and zeromq
content = re.sub(r'self\.connect\(\(self\.ieee802_11_extract_csi_0, 0\), \(self\.zeromq_push_sink_0, 0\)\)\n?', '', content)

with open('wifi_rx.py', 'w') as f:
    f.write(content)
