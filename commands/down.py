from pathlib import Path
import subprocess


def run(args):
    subprocess.check_call(['docker-compose', '-p', args.project_name,
        'down', '--remove-orphans', '--volumes'])


def register(subparsers):
    parser = subparsers.add_parser('down', help='stop virtual waggle environment')
    parser.set_defaults(func=run)
