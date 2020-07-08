import argparse
import json
import subprocess
from pathlib import Path
import sys


parser = argparse.ArgumentParser()
parser.add_argument('plugin_dir')
args = parser.parse_args()

if not Path(args.plugin_dir).is_dir():
    print('error: argument must point to base directory of a plugin')
    sys.exit(1)

try:
    config = json.loads(Path(args.plugin_dir, 'sage.json').read_text())
except FileNotFoundError:
    print('error: plugin is missing sage.json metadata file')
    sys.exit(1)

image_name = 'plugin-{name}:{version}'.format(**config)

# check for expected fields
missing_keys = {'id', 'version', 'name'} - set(config.keys())

if missing_keys:
    print('error: sage.json is missing fields:')
    for k in missing_keys:
        print(f'{k}')
    sys.exit(1)

subprocess.check_output([
    'docker',
    'build',
    '--label', 'waggle.plugin.id={id}'.format(**config),
    '--label', 'waggle.plugin.version={version}'.format(**config),
    '--label', 'waggle.plugin.name={name}'.format(**config),
    '-t', image_name,
    args.plugin_dir,
])

print(image_name)
