#!/usr/bin/env python3
"""Download optional private archives and verify their exact sizes and SHA256 digests."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    metadata = json.loads((ROOT / 'provenance/release_assets.json').read_text())
    assets = {item['key']: item for item in metadata['assets']}
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--asset', action='append', choices=assets)
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    if args.list or not (args.asset or args.all):
        for key, item in assets.items():
            print(f"{key}: {item['name']} ({item['bytes'] / 1048576:.1f} MiB)")
        return
    folder = ROOT / 'downloads'
    folder.mkdir(exist_ok=True)
    for key in (assets if args.all else args.asset):
        item = assets[key]
        path = folder / item['name']
        if not path.exists():
            subprocess.run(['gh', 'release', 'download', metadata['release_tag'],
                            '--repo', metadata['repository'], '--pattern', item['name'],
                            '--dir', str(folder)], check=True)
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise SystemExit(f'Integrity check failed for {path.name}; do not extract it.')
        print(f'Verified: {path.name}')
    print('No archives were extracted and no model was loaded or trained.')


if __name__ == '__main__':
    main()
