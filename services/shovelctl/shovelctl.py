import argparse
import requests
import json
import re
import os
import time

WAGGLE_NODE_ID = os.environ['WAGGLE_NODE_ID'].lower()
WAGGLE_SUB_ID = os.environ['WAGGLE_SUB_ID'].lower()
WAGGLE_BEEHIVE_HOST = os.environ['WAGGLE_BEEHIVE_HOST']

node_uri = (
    'amqp://worker:worker@localhost'
)

beehive_username = f'node-{WAGGLE_NODE_ID}'

beehive_uri = (
    f'amqps://{beehive_username}@{WAGGLE_BEEHIVE_HOST}:23181'
    '?auth_mechanism=external'
    '&cacertfile=/etc/waggle/cacert.pem'
    '&certfile=/etc/waggle/cert.pem'
    '&keyfile=/etc/waggle/key.pem'
    '&verify=verify_peer'
    '&connect_timeout=60000'
    '&server_name_indication=disable'
    # '&heartbeat=60'
)

configs = {
    'push-to-beehive-v1': {
        'src-uri': node_uri,
        'src-queue': 'data',
        'dest-uri': beehive_uri,
        'dest-exchange': 'data-pipeline-in',
        'publish-properties': {
            'delivery_mode': 2,
            'user_id': beehive_username,
            # old data path uses short node ID
            'reply_to': WAGGLE_NODE_ID[-12:],
        },
        'reconnect-delay': 60,
    },
    'push-to-beehive-v2': {
        'src-uri': node_uri,
        'src-queue': 'to-beehive',
        'dest-uri': beehive_uri,
        'dest-exchange': 'messages',
        'publish-properties': {
            'delivery_mode': 2,
            'user_id': beehive_username,
        },
        'reconnect-delay': 60,
    },
    'pull-from-beehive-v2': {
        'src-uri': beehive_uri,
        'src-queue': f'to-{beehive_username}',
        'dest-uri': node_uri,
        'dest-exchange': 'to-node',
        'publish-properties': {
            'delivery_mode': 2,
        },
        'reconnect-delay': 60,
    },
}

auth = ('admin', 'admin')


def wait_for_rabbitmq():
    while True:
        print('waiting for rabbitmq...', flush=True)
        try:
            return requests.get(f'http://rabbitmq:15672/api/')
        except requests.exceptions.ConnectionError:
            time.sleep(5)


def enable_shovels():
    print(
        f'enabling shovels for {WAGGLE_NODE_ID}:{WAGGLE_SUB_ID} on {WAGGLE_BEEHIVE_HOST}.', flush=True)

    wait_for_rabbitmq()

    with requests.Session() as session:
        session.auth = auth

        for name, config in configs.items():
            r = session.put(f'http://rabbitmq:15672/api/parameters/shovel/%2f/{name}', json={
                'value': config,
            })
            print(f'enabled shovel {name}')


def disable_shovels():
    print(
        f'disabling shovels for {WAGGLE_NODE_ID}:{WAGGLE_SUB_ID} on {WAGGLE_BEEHIVE_HOST}.', flush=True)

    wait_for_rabbitmq()

    with requests.Session() as session:
        session.auth = auth

        for name in configs.keys():
            r = session.delete(
                f'http://rabbitmq:15672/api/parameters/shovel/%2f/{name}')
            print(f'disabled shovel {name}')


actions = {
    'enable': enable_shovels,
    'disable': disable_shovels,
}

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=actions.keys())
args = parser.parse_args()
actions[args.action]()
