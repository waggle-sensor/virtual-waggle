import argparse
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('plugins', nargs='+')
args = parser.parse_args()

images = []

for plugin in args.plugins:
    config = json.loads(Path(plugin, 'sage.json').read_text())

    image_name = 'plugin-{name}:{version}'.format(**config)

    subprocess.check_output([
        'docker',
        'build',
        '--label', 'waggle.plugin.id={id}'.format(**config),
        '--label', 'waggle.plugin.version={version}'.format(**config),
        '--label', 'waggle.plugin.name={name}'.format(**config),
        '-t', image_name,
        plugin,
    ])

    images.append(image_name)

print(*images)
