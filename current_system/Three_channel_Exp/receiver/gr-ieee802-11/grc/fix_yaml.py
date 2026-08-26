import yaml
with open('ieee802_11_extract_csi.block.yml', 'r') as f:
    data = yaml.safe_load(f)

if 'outputs' in data:
    del data['outputs']

class CustomDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

with open('ieee802_11_extract_csi.block.yml', 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, Dumper=CustomDumper)
