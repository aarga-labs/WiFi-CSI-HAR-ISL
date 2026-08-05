import yaml
filename = 'wifi_rx.grc'

with open(filename, 'r') as f:
    data = yaml.safe_load(f)

for block in data['blocks']:
    if block['name'] == 'zeromq_push_sink_0':
        block['parameters']['affinity'] = ''
        block['parameters']['alias'] = ''
        block['parameters']['comment'] = ''

class CustomDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

with open(filename, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, Dumper=CustomDumper)
