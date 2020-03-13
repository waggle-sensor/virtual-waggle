import argparse
import requests
import subprocess
import ssl
from pathlib import Path
import re
import os
from hashlib import sha256
from base64 import b64encode
import subprocess
import json
import sys

WAGGLE_NODE_ID = os.environ['WAGGLE_NODE_ID'].lower()
WAGGLE_SUB_ID = os.environ['WAGGLE_SUB_ID'].lower()


def generate_random_password():
    return ssl.RAND_bytes(20).hex()


def rabbitmq_password_hash(password):
    salt = bytes([0x90, 0x8d, 0xc6, 0x0a])
    data = password.encode()
    return b64encode(salt + sha256(salt + data).digest()).decode()


# move into unit test
assert rabbitmq_password_hash(
    'test12') == 'kI3GCqW5JLMJa4iX1lo7X4D6XbYqlLgxIs30+P6tENUV2POR'


def get_rabbitmq_user(session, username):
    return session.get(f'http://localhost:15672/api/users/{username}').json()


def update_rabbitmq_user(session, username, password):
    user = get_rabbitmq_user(session, username)

    password_hash = rabbitmq_password_hash(password)

    if user.get('password_hash') == password_hash:
        return

    session.put(f'http://localhost:15672/api/users/{username}', json={
        'password_hash': password_hash,
        'tags': '',
    })


def update_rabbitmq_user_permissions(session, username, permissions):
    session.put(f'http://localhost:15672/api/permissions/%2f/{username}',
                json=permissions)


def setup_rabbitmq_for_service(service):
    username = service['plugin_username']
    password = service['plugin_password']

    plugin_queue = f'to-{username}'

    with requests.Session() as session:
        session.auth = ('admin', 'admin')

        update_rabbitmq_user(session, username, password)

        update_rabbitmq_user_permissions(session, username, permissions={
            'configure': f'^{plugin_queue}$',
            'write': f'^messages|data$',
            'read': f'^{plugin_queue}$',
        })

        # create queue to message to plugin

        r = session.put(f'http://localhost:15672/api/queues/%2f/{plugin_queue}', json={
            'durable': True,
        })

        assert r.status_code in [201, 204]

        # add binding for nodeid prefix
        r = session.post(f'http://localhost:15672/api/bindings/%2f/e/to-node/q/{plugin_queue}', json={
            'routing_key': f'{WAGGLE_NODE_ID}.{WAGGLE_SUB_ID}.{plugin_id}.{plugin_version}.{plugin_instance}'.format(**service),
        })

        assert r.status_code in [201, 204]


def get_plugin_id_for_image(image):
    output = subprocess.check_output(
        ['docker', 'run', '--rm', image, 'printenv', 'WAGGLE_PLUGIN_ID'])
    return int(output)


def get_plugin_labels_for_image(image, domain):
    output = subprocess.check_output([
        'docker',
        'inspect',
        '--format',
        '{{ range $k, $v := .Config.Labels }} {{ $k }}={{ $v }}, {{ end }}',
        image
    ])
    return [label.split('=')[1] for label in output.decode().strip().split(',') if domain in label]


parser = argparse.ArgumentParser()
parser.add_argument('plugins', nargs='*')
args = parser.parse_args()

services = []

for plugin in args.plugins:
    match = re.match(r'waggle/plugin-(\S+):(\S+)', plugin)
    plugin_name = match.group(1)
    plugin_version = match.group(2)

    try:
        plugin_id = get_plugin_id_for_image(plugin)
    except Exception:
        print(f'Missing WAGGLE_PLUGIN_ID for plugin {plugin}')
        sys.exit(1)

    plugin_instance = 0

    username = f'plugin-{plugin_id}-{plugin_version}-{plugin_instance}'
    password = generate_random_password()

    Path('private', 'plugins', username).mkdir(parents=True, exist_ok=True)
    Path('private', 'plugins', username, 'plugin.credentials').write_text(f'''
    [credentials]
    username={username}
    password={password}
    '''.strip())

    service = {
        'image': plugin,
        'name': username,
        'plugin_id': plugin_id,
        'plugin_version': plugin_version,
        'plugin_instance': plugin_instance,
        'plugin_username': username,
        'plugin_password': password,
    }
    devices = get_plugin_labels_for_image(plugin, "waggle.devices")
    volumes = get_plugin_labels_for_image(plugin, "waggle.volumes")
    service.update({
        'plugin_devices': devices,
        'plugin_volumes': volumes
    })
    services.append(service)


for service in services:
    setup_rabbitmq_for_service(service)


def generate_compose_for_services(services):
    return {
        'version': '3',
        'services': generate_services_block(services),
    }


def generate_services_block(services):
    return {service['name']: generate_service_block(service)}


def generate_service_block(service):
    return {
        'image': service['image'],
        'restart': 'always',
        'networks': ['waggle'],
        'environment': [
            "WAGGLE_PLUGIN_HOST=rabbitmq",
            "WAGGLE_PLUGIN_ID={plugin_id}".format(**service),
            "WAGGLE_PLUGIN_VERSION={plugin_version}".format(**service),
            "WAGGLE_PLUGIN_INSTANCE={plugin_instance}".format(**service),
            "WAGGLE_PLUGIN_USERNAME={plugin_username}".format(**service),
            "WAGGLE_PLUGIN_PASSWORD={plugin_password}".format(**service),
        ],
        'volumes': generate_volumes_block(service),
    }


def generate_volumes_block(service):
    return (
        ["${{WAGGLE_ETC_ROOT}}/plugins/{plugin_username}/plugin.credentials:/plugin/plugin.credentials:ro".format(**service)] +
        ['{0}:{0}'.format(device) for device in service['plugin_devices']] +
        ['{0}:{0}'.format(device) for device in service['plugin_volumes']]
    )


with open('docker-compose.plugins.yml', 'w') as file:
    json.dump(generate_compose_for_services(services), file, indent=True)

# update running services
subprocess.check_call([
    'docker-compose',
    '-f', 'docker-compose.yml',
    '-f', 'docker-compose.plugins.yml',
    'up',
    '-d',
    '--remove-orphans',  # removes plugins no longer enabled
])
