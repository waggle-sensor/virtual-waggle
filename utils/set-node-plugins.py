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
            'routing_key': '{WAGGLE_NODE_ID}.{WAGGLE_SUB_ID}.plugin.{plugin_id}.{plugin_version}.{plugin_instance}'.format(WAGGLE_NODE_ID=WAGGLE_NODE_ID, WAGGLE_SUB_ID=WAGGLE_SUB_ID, **service),
        })

        assert r.status_code in [201, 204]


def get_docker_image_label(image, label):
    output = subprocess.check_output([
        'docker', 'inspect', '--format', f'{{{{ index .Config.Labels "{label}" }}}}', image])
    return output.decode().strip()


def get_plugin_id_for_image(image):
    return int(get_docker_image_label(image, 'waggle.plugin.id'))


def get_plugin_version_for_image(image):
    return get_docker_image_label(image, 'waggle.plugin.version')


def get_plugin_labels_for_image(image, domain):
    output = subprocess.check_output([
        'docker',
        'inspect',
        '--format',
        '{{ range $k, $v := .Config.Labels }} {{ $k }}={{ $v }}, {{ end }}',
        image
    ])
    return [label.split('=')[1] for label in output.decode().strip().split(',') if domain in label]


def get_plugin_service(plugin):
    plugin_id = get_plugin_id_for_image(plugin)
    plugin_version = get_plugin_version_for_image(plugin)
    plugin_instance = 0

    username = f'plugin-{plugin_id}-{plugin_version}-{plugin_instance}'
    password = generate_random_password()

    return {
        'image': plugin,
        'name': username,
        'plugin_id': plugin_id,
        'plugin_version': plugin_version,
        'plugin_instance': plugin_instance,
        'plugin_username': username,
        'plugin_password': password,
        'plugin_devices': get_plugin_labels_for_image(plugin, 'waggle.devices'),
        'plugin_volumes': get_plugin_labels_for_image(plugin, 'waggle.volumes'),
    }


def generate_compose_for_services(services):
    return {
        'version': '3',
        'services': generate_services_block(services),
    }


def generate_services_block(services):
    return {service['name']: generate_service_block(service) for service in services}


def generate_service_block(service):
    return {
        'image': service['image'],
        'restart': 'always',
        'networks': ['waggle'],
        'env_file': ['waggle-node.env'],
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
        ['{0}:{0}'.format(device) for device in service['plugin_devices']] +
        ['{0}:{0}'.format(device) for device in service['plugin_volumes']]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plugins', nargs='*')
    args = parser.parse_args()

    services = [get_plugin_service(plugin) for plugin in args.plugins]

    for service in services:
        setup_rabbitmq_for_service(service)

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

    # expected output is single line containing all service names
    print(*[service['name'] for service in services])


if __name__ == '__main__':
    main()
