import log
import sys
from pathlib import Path
import subprocess
import json


platform_table = {
    ('linux', 'x86_64'): 'linux/amd64',
    ('linux', 'amd64'): 'linux/amd64',
}

expected_config_params = [
    ('id', int),
    ('version', str),
    ('name', str),
]


def get_docker_info():
    return json.loads(subprocess.check_output(['docker', 'info', '-f', '{{json .}}']))


def get_platform():
    info = get_docker_info()

    try:
        key = (info['OSType'], info['Architecture'])
    except KeyError:
        log.fatal('Could not find OSType or Architecture in docker info.')

    try:
        return platform_table[key]
    except KeyError:
        log.fatal(f'No platform found for "{key}".')


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
        log.fatal(f'Plugin path "{plugin_dir}" does not exist.')
    if not plugin_dir.is_dir():
        log.fatal('Argument must point to base directory of a plugin.')
    try:
        return json.loads((plugin_dir / 'sage.json').read_text())
    except FileNotFoundError:
        log.fatal('Plugin is missing sage.json metadata file.')


def get_build_command_for_config(args, config):
    raise_for_invalid_config(config)
    image_name = get_image_name_for_config(config)

    # get source for platform
    platform = get_platform()

    try:
        source = next(s for s in config['sources']
                      if platform in s['architectures'])
    except StopIteration:
        log.fatal(f'error: no source found for platform "{platform}"')

    user_args = (get_build_args_from_list(args.build_arg) +
                 get_build_args_from_dict(source.get('build_args', {})))

    return [
        'docker',
        'build',
        *user_args,
        '--label', 'waggle.plugin.config={}'.format(json.dumps(config, separators=(',', ':'))),
        '--label', 'waggle.plugin.id={id}'.format(**config),
        '--label', 'waggle.plugin.version={version}'.format(**config),
        '--label', 'waggle.plugin.name={name}'.format(**config),
        '-t', image_name,
        str(args.plugin_dir),
    ]


def run(args):
    config = load_sage_config_for_plugin(args.plugin_dir)
    cmd = get_build_command_for_config(args, config)
    # print explicit build command used. helpful for debugging.
    cmdstr = ' '.join(cmd)
    print(f'Running build command\n{cmdstr}', file=sys.stderr)

    # exec docker build and print resulting image name.
    subprocess.check_call(cmd, stdout=sys.stderr, stderr=sys.stderr)
    print(get_image_name_for_config(config))


def register(subparsers):
    parser = subparsers.add_parser('build', help='build plugin for virtual waggle from a directory')
    parser.add_argument('--build-arg', action='append', default=[])
    parser.add_argument('plugin_dir', type=Path, help='base directory of plugin to build')
    parser.set_defaults(func=run)
