import log
import sys
from pathlib import Path
import subprocess
import re
from shutil import copytree

TEMPLATE_DIR = Path(sys.argv[0]).parent / 'templates'
TEMPLATE_NAMES = [p.name for p in TEMPLATE_DIR.glob('*/')]

sage_json_template = '''{{
    "id": 1000,
    "name": "{name}",
    "description": "My cool new plugin called {name}.",
    "version": "0.0.1",
    "sources": [
        {{
            "architectures": ["linux/amd64", "linux/arm/v7", "linux/arm64"],
            "build_args": {{}}
        }}
    ]
}}
'''


def plugin_name_valid(s):
    return re.match('[a-z0-9_-]+$', s) is not None


def run(args):
    if not plugin_name_valid(args.name):
        log.fatal(f'Plugin names can only contain lowercase letters, numbers, _ and -.')

    plugin_dir = Path(f'plugin-{args.name}')

    try:
        copytree(TEMPLATE_DIR / args.template, plugin_dir)
    except FileExistsError:
        log.fatal(f'Plugin directory {plugin_dir} already exists.')

    (plugin_dir / 'sage.json').write_text(sage_json_template.format(name=args.name))


def register(subparsers):
    parser = subparsers.add_parser('newplugin', help='generates a new plugin')
    parser.add_argument('-t', '--template', default='simple', choices=TEMPLATE_NAMES, help='plugin template to use')
    parser.add_argument('name', help='name of plugin')
    parser.set_defaults(func=run)
