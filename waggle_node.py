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
import re
from shutil import copytree
import unittest

TEMPLATE_DIR = Path(sys.argv[0]).parent / 'templates'
TEMPLATE_NAMES = [p.name for p in TEMPLATE_DIR.glob('*/')]


def notice(msg):
    print(f'\033[94mNOTICE: {msg}\033[00m', file=sys.stderr)


def warning(msg):
    print(f'\033[93mWARNING: {msg}\033[00m', file=sys.stderr)


def fatal(msg):
    print(f'\033[91mERROR: {msg}\033[00m', file=sys.stderr)
    sys.exit(1)


def run_quiet(*args, **kwargs):
    return subprocess.run(*args, **kwargs, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def command_up(args):
    if not Path('private/register.pem').exists():
        warning('No registration key found. Running in local only mode.')
    
    extra_args = []
    if args.debug:
        extra_args += ['-f', 'docker-compose.debug.yml']
        notice('RabbitMQ management is available at: http://127.0.0.1:15672')
        notice('Playback server is available at: http://127.0.0.1:8090')
    if args.ros:
        extra_args += ['-f', 'docker-compose.ros.yml']
        notice('ROS plugins should use ROS_MASTER_URI=http://ros-master:11311')

    subprocess.check_call([
        'docker-compose',
        '-p', args.project_name,
        '-f', 'docker-compose.yml', # explicitly put this compose file first, since others can be in extra_args
        *extra_args,
        'up', '-d', '--remove-orphans'])


def remove_file_if_exists(path):
    try:
        path.unlink()
        print(f'Cleaned up {path}')
    except FileNotFoundError:
        pass


def get_docker_info():
    return json.loads(subprocess.check_output(['docker', 'info', '-f', '{{json .}}']))


platform_table = {
    ('linux', 'x86_64'): 'linux/amd64',
    ('linux', 'amd64'): 'linux/amd64',
}


def get_platform():
    info = get_docker_info()

    try:
        key = (info['OSType'], info['Architecture'])
    except KeyError:
        fatal('Could not find OSType or Architecture in docker info.')

    try:
        return platform_table[key]
    except KeyError:
        fatal(f'No platform found for "{key}".')


def command_down(args):
    subprocess.check_call(['docker-compose', '-p', args.project_name, 'down', '--remove-orphans'])
    remove_file_if_exists(Path('private/key.pem'))
    remove_file_if_exists(Path('private/cert.pem'))
    remove_file_if_exists(Path('private/cacert.pem'))
    remove_file_if_exists(Path('private/reverse_ssh_port'))


def command_logs(args):
    subprocess.check_call(['docker-compose', '-p', args.project_name, 'logs', '-f'])


def generate_random_password():
    return secrets.token_hex(20)


def get_docker_image_labels(image):
    results = json.loads(subprocess.check_output(['docker', 'inspect', image]))
    return {k: v for r in results for k, v in r['ContainerConfig']['Labels'].items()}


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


def command_run(args):
    if not has_plugin(args.plugin):
        print(
            f'Did not find plugin {args.plugin} locally. Pulling from remote...')
        try:
            subprocess.check_call(['docker', 'pull', args.plugin])
        except subprocess.CalledProcessError:
            fatal(f'Failed to pull plugin {args.plugin}.')

    labels = get_docker_image_labels(args.plugin)

    plugin_id = int(labels['waggle.plugin.id'])
    plugin_version = labels['waggle.plugin.version']
    plugin_name = labels['waggle.plugin.name']
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


expected_config_params = [
    ('id', int),
    ('version', str),
    ('name', str),
]


def raise_for_invalid_config(config):
    for key, type in expected_config_params:
        if key not in config:
            raise KeyError(f'sage.json is missing key "{key}"')
        if not isinstance(config[key], type):
            raise ValueError(f'sage.json key "{key}" must be of type "{type}"')


def get_build_args_from_list(ls):
    results = []
    for a in ls:
        results += ['--build-arg', a]
    return results


def get_build_args_from_dict(d):
    return get_build_args_from_list(f'{k}={v}' for k, v in d.items())


def get_image_name_for_config(config):
    return 'plugin-{name}:{version}'.format(**config)


def load_sage_config_for_plugin(plugin_dir):
    if not plugin_dir.exists():
        fatal(f'Plugin path "{plugin_dir}" does not exist.')
    if not plugin_dir.is_dir():
        fatal('Argument must point to base directory of a plugin.')
    try:
        return json.loads((plugin_dir / 'sage.json').read_text())
    except FileNotFoundError:
        fatal('Plugin is missing sage.json metadata file.')


def get_build_command_for_config(args, config):
    raise_for_invalid_config(config)
    image_name = get_image_name_for_config(config)

    # get source for platform
    platform = get_platform()

    try:
        source = next(s for s in config['sources']
                      if platform in s['architectures'])
    except StopIteration:
        fatal(f'error: no source found for platform "{platform}"')

    user_args = (get_build_args_from_list(args.build_arg) +
                 get_build_args_from_dict(source.get('build_args', {})))

    return [
        'docker',
        'build',
        *user_args,
        '--label', 'waggle.plugin.id={id}'.format(**config),
        '--label', 'waggle.plugin.version={version}'.format(**config),
        '--label', 'waggle.plugin.name={name}'.format(**config),
        '-t', image_name,
        str(args.plugin_dir),
    ]


def command_build(args):
    config = load_sage_config_for_plugin(args.plugin_dir)
    cmd = get_build_command_for_config(args, config)
    # print explicit build command used. helpful for debugging.
    cmdstr = ' '.join(cmd)
    print(f'Running build command\n{cmdstr}', file=sys.stderr)

    # exec docker build and print resulting image name.
    subprocess.check_call(cmd, stdout=sys.stderr, stderr=sys.stderr)
    print(get_image_name_for_config(config))


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


def command_new_plugin(args):
    if not plugin_name_valid(args.name):
        fatal(f'Plugin names can only contain lowercase letters, numbers, _ and -.')

    plugin_dir = Path(f'plugin-{args.name}')

    try:
        copytree(TEMPLATE_DIR / args.template, plugin_dir)
    except FileExistsError:
        fatal(f'Plugin directory {plugin_dir} already exists.')

    (plugin_dir / 'sage.json').write_text(sage_json_template.format(name=args.name))


def command_report(args):
    print('=== Config Info ===')
    print('Registration Key Exists:', 'Yes' if Path(
        'private/register.pem').exists() else 'No')
    print('Node ID:', os.environ.get('WAGGLE_NODE_ID'))
    print('Beehive Host:', os.environ.get('WAGGLE_BEEHIVE_HOST'))
    print()

    print('=== Playback Server Logs ===')
    subprocess.run(['docker-compose', '-p', args.project_name,
                    'logs', 'playback'])
    print()

    print('=== RabbitMQ Queue Status ===')
    subprocess.run(['docker-compose', '-p', args.project_name,
                    'exec', 'rabbitmq', 'rabbitmqctl', 'list_queues'])
    print()

    print('=== RabbitMQ Shovel Status ===')
    subprocess.run(['docker-compose', '-p', args.project_name,
                    'exec', 'rabbitmq', 'rabbitmqctl', 'eval', 'rabbit_shovel_status:status().'])
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=lambda args: parser.print_help())
    parser.add_argument('-p', '--project-name',
                        default=os.path.basename(os.getcwd()), help='specify project name (default: directory name)')

    subparsers = parser.add_subparsers()

    parser_up = subparsers.add_parser(
        'up', help='start virtual waggle environment')
    parser_up.add_argument('--debug', action='store_true', help='open local service ports for debugging')
    parser_up.add_argument('--ros', action='store_true', help='run local ros master')
    parser_up.set_defaults(func=command_up)

    parser_down = subparsers.add_parser(
        'down', help='stop virtual waggle environment')
    parser_down.set_defaults(func=command_down)

    parser_logs = subparsers.add_parser(
        'logs', help='show virtual waggle system logs')
    parser_logs.add_argument('-f', action='store_true', help='follow logs')
    parser_logs.set_defaults(func=command_logs)

    parser_report = subparsers.add_parser(
        'report', help='show virtual waggle system report for debugging')
    parser_report.set_defaults(func=command_report)

    parser_build = subparsers.add_parser(
        'build', help='build plugin for virtual waggle from a directory')
    parser_build.add_argument('--build-arg', action='append', default=[])
    parser_build.add_argument(
        'plugin_dir', type=Path, help='base directory of plugin to build')
    parser_build.set_defaults(func=command_build)

    parser_run = subparsers.add_parser(
        'run', help='runs a plugin inside virtual waggle environment')
    parser_run.add_argument('plugin', help='plugin to run')
    parser_run.add_argument('plugin_args', nargs=argparse.REMAINDER,
                            help='arguments to pass to plugin')
    parser_run.set_defaults(func=command_run)

    parser_new_plugin = subparsers.add_parser(
        'newplugin', help='generates a new plugin')
    parser_new_plugin.add_argument(
        '-t', '--template', default='simple', choices=TEMPLATE_NAMES, help='plugin template to use')
    parser_new_plugin.add_argument('name', help='name of plugin')
    parser_new_plugin.set_defaults(func=command_new_plugin)

    args = parser.parse_args()

    try:
        args.func(args)
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)


if __name__ == '__main__':
    main()
