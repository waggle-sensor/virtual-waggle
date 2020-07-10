#!/usr/bin/env python3
import argparse
import os
import os.path
import subprocess
import secrets
from hashlib import sha256
from base64 import b64encode
import sys
from pathlib import Path
import json


def fatal(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)
    sys.exit(1)


def command_up(args):
    volume = os.path.join(os.getcwd(), 'private')

    network = f'{args.project}.waggle'

    print('setting up network')
    subprocess.run([
        'docker', 'network', 'create', network], capture_output=True)

    print('setting up rabbitmq')
    subprocess.run([
        'docker', 'run', '-d',
        '--name', f'{args.project}.rabbitmq',
        '--network', network,
        '--network-alias', 'rabbitmq',
        '--env-file', 'waggle-node.env',
        '--restart', 'always',
        '-v', f'{volume}:/etc/waggle:ro',
        'waggle/rabbitmq:nc',
    ], capture_output=True)

    print('setting up registration')
    subprocess.run([
        'docker', 'run', '-d',
        '--name', f'{args.project}.registration',
        '--network', network,
        '--env-file', 'waggle-node.env',
        '--restart', 'on-failure',
        '-v', f'{volume}:/etc/waggle',
        'waggle/registration',
    ], capture_output=True)


def command_down(args):
    # get all process IDs for this VW
    ids = subprocess.check_output(
        ['docker', 'ps', '-q', '-a', '-f', f'name={args.project}.']).decode().split()
    # remove all process for IDs
    subprocess.run(['docker', 'rm', '-f'] + ids, capture_output=True)


def command_logs(args):
    subprocess.run([
        'docker', 'logs', '-f', f'{args.project}.rabbitmq', f'{args.project}.registration'])


def generate_random_password():
    return secrets.token_hex(20)


# TODO Save in case we move back to API instead of rabbitmqctl
# def rabbitmq_password_hash(password):
#     salt = bytes([0x90, 0x8d, 0xc6, 0x0a])
#     data = password.encode()
#     return b64encode(salt + sha256(salt + data).digest()).decode()


def get_docker_image_label(image, label):
    return subprocess.check_output([
        'docker',
        'inspect',
        '--format', f'{{{{ index .Config.Labels "{label}" }}}}',
        image]).decode().strip()


def setup_rabbitmq_user(args, username, password):
    subprocess.run([
        'docker', 'exec', f'{args.project}.rabbitmq',
        'rabbitmqctl',
        'add_user',
        username,
        password,
    ], capture_output=True)

    subprocess.run([
        'docker', 'exec', f'{args.project}.rabbitmq',
        'rabbitmqctl',
        'change_password',
        username,
        password,
    ], capture_output=True)

    subprocess.run([
        'docker', 'exec', f'{args.project}.rabbitmq',
        'rabbitmqctl',
        'set_permissions',
        username,
        '.*',
        '.*',
        '.*',
    ], capture_output=True)


def command_run(args):
    plugin_id = int(get_docker_image_label(args.plugin, 'waggle.plugin.id'))
    plugin_version = get_docker_image_label(
        args.plugin, 'waggle.plugin.version')
    plugin_name = get_docker_image_label(args.plugin, 'waggle.plugin.name')
    plugin_instance = 0
    plugin_username = f'plugin-{plugin_id}-{plugin_version}-{plugin_instance}'
    plugin_password = generate_random_password()

    print(f'Setting up credentials for {args.plugin}')
    setup_rabbitmq_user(args, plugin_username, plugin_password)

    network = f'{args.project}.waggle'
    name = f'{args.project}.{plugin_name}-{plugin_version}-{plugin_instance}'

    subprocess.run(['docker', 'rm', '-f', name], capture_output=True)

    try:
        print(f'Running {args.plugin}\n')

        subprocess.run([
            'docker', 'run', '-it',
            '--name', name,
            '--network', network,
            '--env-file', 'waggle-node.env',
            '--restart', 'on-failure',
            '-e', f'WAGGLE_PLUGIN_ID={plugin_id}',
            '-e', f'WAGGLE_PLUGIN_VERSION={plugin_version}',
            '-e', f'WAGGLE_PLUGIN_INSTANCE={plugin_instance}',
            '-e', f'WAGGLE_PLUGIN_USERNAME={plugin_username}',
            '-e', f'WAGGLE_PLUGIN_PASSWORD={plugin_password}',
            args.plugin,
        ])
    finally:
        print(f'Cleaning up {args.plugin}')
        subprocess.run(['docker', 'rm', '-f', name], capture_output=True)


def command_build(args):
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

    subprocess.run([
        'docker',
        'build',
        '--label', 'waggle.plugin.id={id}'.format(**config),
        '--label', 'waggle.plugin.version={version}'.format(**config),
        '--label', 'waggle.plugin.name={name}'.format(**config),
        '-t', image_name,
        str(args.plugin_dir),
    ], stdout=sys.stderr, stderr=sys.stderr)

    print(image_name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--project',
                        default=os.path.basename(os.getcwd()), help='project')

    subparsers = parser.add_subparsers()

    parser_up = subparsers.add_parser('up')
    parser_up.set_defaults(func=command_up)

    parser_down = subparsers.add_parser('down')
    parser_down.set_defaults(func=command_down)

    parser_logs = subparsers.add_parser('logs')
    parser_logs.add_argument('-f', action='store_true', help='follow logs')
    parser_logs.add_argument('plugin', help='plugin to')
    parser_logs.set_defaults(func=command_logs)

    parser_build = subparsers.add_parser('build')
    parser_build.add_argument(
        'plugin_dir', type=Path, help='base directory of plugin to build')
    parser_build.set_defaults(func=command_build)

    parser_run = subparsers.add_parser('run')
    parser_run.add_argument('plugin', help='plugin to run')
    parser_run.set_defaults(func=command_run)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()