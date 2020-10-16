import sys
from pathlib import Path
import subprocess


def run(args):
    extra_args = []
    if args.f:
        extra_args += ['-f']
    if args.tail:
        extra_args += ['--tail', args.tail]
    subprocess.check_call(['docker-compose', '-p', args.project_name, 'logs'] + extra_args)


def register(subparsers):
    parser = subparsers.add_parser('logs', help='show virtual waggle system logs')
    parser.add_argument('-f', action='store_true', help='follow logs')
    parser.add_argument('--tail', help='start at tail of logs')
    parser.set_defaults(func=run)
