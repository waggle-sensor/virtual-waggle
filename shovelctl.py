import argparse
import requests
import json
import re
import utils


username = utils.read_username_from_cert()
match = re.search(r'node\-([0-9a-fA-F]{16})', username)
node_id = match.group(1)[-12:]

# beehive_hostname = 'beehive1.mcs.anl.gov'
beehive_hostname = 'host.docker.internal'

beehive_uri = (
    f'amqps://{username}@{beehive_hostname}:23181'
    '?auth_mechanism=external'
    '&cacertfile=/etc/waggle/cacert.pem'
    '&certfile=/etc/waggle/cert.pem'
    '&keyfile=/etc/waggle/key.pem'
    '&verify=verify_peer'
    '&connect_timeout=60000'
    '&server_name_indication=disable'
    # '&heartbeat=60'
)

node_uri = (
    'amqp://worker:worker@localhost'
)

configs = {
    'push-to-beehive-v1': {
        'src-uri': node_uri,
        'src-queue': 'data',
        'dest-uri': beehive_uri,
        'dest-exchange': 'data-pipeline-in',
        'publish-properties': {
            'delivery_mode': 2,
            'user_id': username,
            'reply_to': node_id,
        },
    },
    'push-to-beehive-v2': {
        'src-uri': node_uri,
        'src-queue': 'to-beehive',
        'dest-uri': beehive_uri,
        'dest-exchange': 'messages',
        'publish-properties': {
            'delivery_mode': 2,
            'user_id': username,
        },
    },
    'pull-from-beehive-v2': {
        'src-uri': beehive_uri,
        'src-queue': f'to-{username}',
        'dest-uri': node_uri,
        'dest-exchange': 'to-node',
        'publish-properties': {
            'delivery_mode': 2,
        }
    },
}

auth = ('admin', 'admin')


def enable_shovels():
    with requests.Session() as session:
        session.auth = auth

        for name, config in configs.items():
            r = session.put(
                f'http://localhost:15672/api/parameters/shovel/%2f/{name}', json={
                    'value': config,
                })
            print(r.text)


def disable_shovels():
    with requests.Session() as session:
        session.auth = auth

        for name in configs.keys():
            r = session.delete(
                f'http://localhost:15672/api/parameters/shovel/%2f/{name}')
            print(r.text)


actions = {
    'enable': enable_shovels,
    'disable': disable_shovels,
}

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=actions.keys())
args = parser.parse_args()
actions[args.action]()
