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

WAGGLE_NODE_ID = os.environ['WAGGLE_NODE_ID']
WAGGLE_SUB_ID = os.environ['WAGGLE_SUB_ID']


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
            'configure': f'^$',
            'write': f'^messages|data$',
            'read': f'^{plugin_queue}$',
        })

        # create queue to message to plugin

        r = session.put(f'http://localhost:15672/api/queues/%2f/{plugin_queue}', json={
            'durable': True,
        })

        assert r.status_code in [201, 204]

        # add binding for nodeid prefix
        # TODO get proper node ID
        # TODO get proper component ID
        r = session.post(f'http://localhost:15672/api/bindings/%2f/e/to-node/q/{plugin_queue}', json={
            'routing_key': f'{WAGGLE_NODE_ID}.{WAGGLE_SUB_ID}.{plugin_id}.{plugin_version}.{plugin_instance}'.format(**service),
        })

        assert r.status_code in [201, 204]


# ah... we need a way to map between names and internal IDs now...

# username must match
# 'plugin-(id)-(version)-(instance)'
# plugin-simple     0.1.0

# ...for now, have to map between internal ids and common name...
plugin_ids = {
    'simple': 37,
}

parser = argparse.ArgumentParser()
parser.add_argument('plugins', nargs='*')
args = parser.parse_args()

services = []

for plugin in args.plugins:
    match = re.match(r'waggle/plugin-(\S+):(\S+)', plugin)
    plugin_name = match.group(1)
    plugin_version = match.group(2)
    plugin_id = plugin_ids[plugin_name]
    plugin_instance = 0

    username = f'plugin-{plugin_id}-{plugin_version}-{plugin_instance}'
    password = generate_random_password()

    Path('private', 'plugins', username).mkdir(parents=True, exist_ok=True)
    Path('private', 'plugins', username, 'plugin.credentials').write_text(f'''
    [credentials]
    username={username}
    password={password}
    '''.strip())

    services.append({
        'image': plugin,
        'name': username,
        'plugin_id': plugin_id,
        'plugin_version': plugin_version,
        'plugin_instance': plugin_instance,
        'plugin_username': username,
        'plugin_password': password,
    })


for service in services:
    setup_rabbitmq_for_service(service)


service_template = '''
  {name}:
    image: {image}
    restart: always
    networks:
      - waggle
    volumes:
      - "${{WAGGLE_ETC_ROOT}}/plugins/{plugin_username}/plugin.credentials:/plugin/plugin.credentials:ro"
    environment:
      - "WAGGLE_PLUGIN_HOST=rabbitmq"
      - "WAGGLE_PLUGIN_ID={plugin_id}"
      - "WAGGLE_PLUGIN_VERSION={plugin_version}"
      - "WAGGLE_PLUGIN_INSTANCE={plugin_instance}"
      - "WAGGLE_PLUGIN_USERNAME={plugin_username}"
      - "WAGGLE_PLUGIN_PASSWORD={plugin_password}"
'''

empty_services_template = '''version: '3'
services: {}'''

template_header = '''version: '3'
services:'''


def generate_compose_file_for_services(services):
    if len(services) == 0:
        return empty_services_template

    template = template_header

    for service in services:
        template += service_template.format(**service)

    return template


# write compose file
Path('docker-compose.plugins.yml').write_text(generate_compose_file_for_services(services))

# update running services
subprocess.check_call([
    'docker-compose',
    '-f', 'docker-compose.system.yml',
    '-f', 'docker-compose.plugins.yml',
    'up',
    '-d',
    '--remove-orphans',  # removes plugins no longer enabled
])
