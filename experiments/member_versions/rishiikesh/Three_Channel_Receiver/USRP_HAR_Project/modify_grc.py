import yaml
import sys

filename = '/home/ubuntu/Desktop/USRP_HAR_Project/wifi_rx.grc'

# GNU Radio 3.8+ uses standard YAML for .grc files
with open(filename, 'r') as f:
    try:
        data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit(1)

# 1. Update center_freq0 to use 'freq'
for block in data['blocks']:
    if block['name'] == 'uhd_usrp_source_0':
        if 'center_freq0' in block['parameters']:
            block['parameters']['center_freq0'] = 'freq'

# 2. Remove foo_wireshark_connector_0 and blocks_file_sink_0
data['blocks'] = [b for b in data['blocks'] if b['name'] not in ['foo_wireshark_connector_0', 'blocks_file_sink_0']]

# 3. Replace blocks_null_sink_0 with zeromq_push_sink_0
for i, block in enumerate(data['blocks']):
    if block['name'] == 'blocks_null_sink_0':
        data['blocks'][i] = {
            'name': 'zeromq_push_sink_0',
            'id': 'zeromq_push_sink',
            'parameters': {
                'affinity': "''",
                'alias': "''",
                'address': 'tcp://127.0.0.1:5555',
                'comment': "''",
                'hwm': '-1',
                'pass_tags': 'True',
                'timeout': '100',
                'type': 'complex',
                'vlen': '52'
            },
            'states': block['states'].copy()
        }
        break

# 4. Update connections
new_connections = []
for conn in data.get('connections', []):
    src, src_port, dst, dst_port = conn
    # Remove connections to/from foo_wireshark_connector
    if src == 'foo_wireshark_connector_0' or dst == 'foo_wireshark_connector_0':
        continue
    if src == 'blocks_file_sink_0' or dst == 'blocks_file_sink_0':
        continue
    
    # Update connections going to null sink
    if dst == 'blocks_null_sink_0':
        dst = 'zeromq_push_sink_0'
        
    new_connections.append([src, src_port, dst, dst_port])

data['connections'] = new_connections

# Dump back to file
class CustomDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

with open(filename, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, Dumper=CustomDumper)

print("GRC file successfully modified!")
