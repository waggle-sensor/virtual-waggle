import log
import argparse
import sys
from pathlib import Path
import subprocess
import secrets
import json


def run_quiet(*args, **kwargs):
    return subprocess.run(*args, **kwargs, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def generate_random_password():
    return secrets.token_hex(20)


def get_docker_image_labels(image):
    output = subprocess.check_output(['docker', 'inspect',
        '-f', '{{ json (or .ContainerConfig.Labels .Config.Labels) }}', image])
    return json.loads(output)


def setup_rabbitmq_user(args, username, password):
    run_quiet([
        'docker-compose', '-p', args.project_name,
        'exec', 'rabbitmq',
        'rabbitmqctl',
        'add_user',
        username,
        password,
    ])

    run_quiet([
        'docker-compose', '-p', args.project_name,
        'exec', 'rabbitmq',
        'rabbitmqctl',
        'change_password',
        username,
        password,
    ])

    run_quiet([
        'docker-compose', '-p', args.project_name,
        'exec', 'rabbitmq',
        'rabbitmqctl',
        'set_permissions',
        username,
        '.*',
        '.*',
        '.*',
    ])


def has_plugin(plugin):
    try:
        run_quiet(['docker', 'inspect', plugin], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def run(args):
    if not has_plugin(args.plugin):
        print(
            f'Did not find plugin {args.plugin} locally. Pulling from remote...')
        try:
            subprocess.check_call(['docker', 'pull', args.plugin])
        except subprocess.CalledProcessError:
            log.fatal(f'Failed to pull plugin {args.plugin}.')

    labels = get_docker_image_labels(args.plugin)

    config = json.loads(labels['waggle.plugin.config'])

    plugin_name = config['name']
    plugin_id = int(config['id'])
    plugin_version = config['version']
    plugin_name = config['name']
    plugin_instance = 0
    plugin_username = f'plugin-{plugin_id}-{plugin_version}-{plugin_instance}'
    plugin_password = generate_random_password()
    # TODO add back in support for devices / volumes

    print(f'Setting up {args.plugin}')
    setup_rabbitmq_user(args, plugin_username, plugin_password)

    network = f'{args.project_name}_waggle'
    name = f'{args.project_name}_plugin-{plugin_name}-{plugin_version}-{plugin_instance}'

    run_quiet(['docker', 'rm', '-f', name])

    data_config_path = Path('./data-config.json').absolute()

    try:
        print(f'Running {args.plugin}\n')

        subprocess.run([
            'docker', 'run', '-it',
            '--name', name,
            '--network', network,
            '--env-file', 'waggle-node.env',
            '--restart', 'on-failure',
            '-e', f'WAGGLE_PLUGIN_NAME={plugin_name}:{plugin_version}',
            '-e', f'WAGGLE_PLUGIN_ID={plugin_id}',
            '-e', f'WAGGLE_PLUGIN_VERSION={plugin_version}',
            '-e', f'WAGGLE_PLUGIN_INSTANCE={plugin_instance}',
            '-e', f'WAGGLE_PLUGIN_USERNAME={plugin_username}',
            '-e', f'WAGGLE_PLUGIN_PASSWORD={plugin_password}',
            '-v', f'{data_config_path}:/run/waggle/data-config.json',
            args.plugin,
            *args.plugin_args,
        ])
    finally:
        print(f'Cleaning up {args.plugin}')
        run_quiet(['docker', 'rm', '-f', name])


def register(subparsers):
    parser = subparsers.add_parser('run', help='runs a plugin inside virtual waggle environment')
    parser.add_argument('plugin', help='plugin to run')
    parser.add_argument('plugin_args', nargs=argparse.REMAINDER, help='arguments to pass to plugin')
    parser.set_defaults(func=run)
