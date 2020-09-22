import log
import sys
from pathlib import Path
import subprocess


def run(args):
    if not Path('private/register.pem').exists():
        log.warning('No registration key found. Running in local only mode.')
    
    extra_args = []

    # Expose ports on host for debugging.
    if args.debug:
        extra_args += ['-f', 'docker-compose.debug.yml']
        log.notice('RabbitMQ management is available at: http://127.0.0.1:15672')
        log.notice('Playback server is available at: http://127.0.0.1:8090')
    
    # Enable ROS master service.
    if args.ros:
        extra_args += ['-f', 'docker-compose.ros.yml']
        log.notice('ROS plugins should use ROS_MASTER_URI=http://ros-master:11311')

    # Deploy docker compose files.
    subprocess.check_call([
        'docker-compose',
        '-p', args.project_name,
        '-f', 'docker-compose.yml', # Explicitly put this compose file first, since others can be in extra_args.
        *extra_args,
        'up', '-d', '--remove-orphans'])


def register(subparsers):
    parser = subparsers.add_parser('up', help='start virtual waggle environment')
    parser.add_argument('--debug', action='store_true', help='open local service ports for debugging')
    parser.add_argument('--ros', action='store_true', help='run local ros master')
    parser.set_defaults(func=run)
