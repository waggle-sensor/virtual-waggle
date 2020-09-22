import sys
from pathlib import Path
import subprocess


def run(args):
    subprocess.check_call(['docker-compose', '-p', args.project_name, 'logs', '-f'])


def register(subparsers):
    parser = subparsers.add_parser('logs', help='show virtual waggle system logs')
    parser.add_argument('-f', action='store_true', help='follow logs')
    parser.set_defaults(func=run)
