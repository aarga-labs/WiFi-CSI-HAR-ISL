#!/usr/bin/env python3
"""Download optional private release assets with the user's own gh authentication; verify SHA256."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    manifest = json.loads((HERE / 'ASSETS.json').read_text())
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list', action='store_true', help='Show optional assets without downloading')
    parser.add_argument('--asset', action='append', choices=list(manifest['assets']), help='Asset key; repeat for several')
    parser.add_argument('--all', action='store_true', help='Download all listed assets (over 1 GB total)')
    args = parser.parse_args()
    if args.list or not (args.asset or args.all):
        for key, asset in manifest['assets'].items():
            print(f"{key}: {asset['name']} ({asset['bytes'] / 1048576:.1f} MiB) — {asset['purpose']}")
        print('Ordinary paper drafting needs none of these downloads. Use --asset KEY when needed.')
        return
    if not shutil.which('gh'):
        parser.error('Install GitHub CLI and authenticate with your own account that has private repository access.')
    output = HERE / 'assets'
    output.mkdir(exist_ok=True)
    for key in (list(manifest['assets']) if args.all else args.asset):
        asset = manifest['assets'][key]
        path = output / asset['name']
        if path.exists():
            if path.stat().st_size != asset['bytes'] or sha256(path) != asset['sha256']:
                raise SystemExit(f'Existing {path} is incomplete/different; move it aside before downloading again.')
            print(f'Already verified: {path.name}')
            continue
        subprocess.run(['gh', 'release', 'download', manifest['release_tag'], '--repo', manifest['repository'], '--pattern', asset['name'], '--dir', str(output)], check=True)
        if path.stat().st_size != asset['bytes'] or sha256(path) != asset['sha256']:
            raise SystemExit(f'Integrity check failed: {path}; do not use or extract it.')
        print(f'Verified SHA256: {path.name}')
    print('Downloads verified. No archives were extracted and no training was run.')


if __name__ == '__main__':
    main()
