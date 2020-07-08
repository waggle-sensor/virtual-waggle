import argparse
import json
import subprocess
from pathlib import Path
import sys


def fatal(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)
    sys.exit(1)


parser = argparse.ArgumentParser()
parser.add_argument('plugin_dir', type=Path)
args = parser.parse_args()

if not args.plugin_dir.is_dir():
    fatal('error: argument must point to base directory of a plugin')

try:
    config = json.loads((args.plugin_dir / 'sage.json').read_text())
except FileNotFoundError:
    fatal('error: plugin is missing sage.json metadata file')

image_name = 'plugin-{name}:{version}'.format(**config)

# check for expected fields
missing_keys = {'id', 'version', 'name'} - set(config.keys())

if missing_keys:
    fatal('error: sage.json is missing fields', missing_keys)

subprocess.check_output([
    'docker',
    'build',
    '--label', 'waggle.plugin.id={id}'.format(**config),
    '--label', 'waggle.plugin.version={version}'.format(**config),
    '--label', 'waggle.plugin.name={name}'.format(**config),
    '-t', image_name,
    str(args.plugin_dir),
])

print(image_name)
