import subprocess
import re
from pathlib import Path
import requests
import time
import os
import logging

logging.basicConfig(level=logging.INFO)

WAGGLE_NODE_ID = os.environ['WAGGLE_NODE_ID']
WAGGLE_BEEHIVE_HOST = os.environ['WAGGLE_BEEHIVE_HOST']


def scan_block(s, head, tail):
    match = re.search(head, s)

    if match is None:
        return None

    s = s[match.start():]

    match = re.search(tail, s)

    if match is None:
        return None

    return s[:match.end()]


def scan_certificate(s):
    return scan_block(s, r'-----BEGIN CERTIFICATE-----', r'-----END CERTIFICATE-----')


def scan_key(s):
    return scan_block(s, r'-----BEGIN RSA PRIVATE KEY-----', r'-----END RSA PRIVATE KEY-----')


def scan_port(s):
    match = re.search(r'PORT=(\d+)', s)

    if match is None:
        return None

    return match.group(1)


def get_request_id():
    while True:
        logging.info('getting request ID...')

        try:
            r = requests.post(
                f'http://{WAGGLE_BEEHIVE_HOST}/api/registration?nodeid={WAGGLE_NODE_ID}').json()
            request_id = r['data']
            logging.info('got request ID %s', request_id)
            return request_id
        except Exception:
            logging.exception('failed to get request ID')
            time.sleep(10)


def get_response_for_request_id(request_id):
    while True:
        logging.info('getting credentials...')

        r = requests.get(
            f'http://{WAGGLE_BEEHIVE_HOST}/api/registration/{request_id}')

        if 'pending' in r.text:
            time.sleep(10)
            continue

        return r.text


should_exist = [
    Path('/etc/waggle/cacert.pem'),
    Path('/etc/waggle/cert.pem'),
    Path('/etc/waggle/key.pem'),
    Path('/etc/waggle/reverse_ssh_port'),
]


def register_if_needed():
    # TODO check if credentials are valid
    if all(path.exists() for path in should_exist):
        logging.info('credentials already exist. done!')
        return

    logging.info('registering node %s on beehive %s',
                 WAGGLE_NODE_ID, WAGGLE_BEEHIVE_HOST)

    r = requests.get(f'http://{WAGGLE_BEEHIVE_HOST}:24181/certca')
    cacert = scan_certificate(r.text)
    logging.info('got ca certificate')

    request_id = get_request_id()

    response = get_response_for_request_id(request_id)
    cert = scan_certificate(response)
    key = scan_key(response)
    port = scan_port(response)

    Path('/etc/waggle/cacert.pem').write_text(cacert)
    Path('/etc/waggle/cert.pem').write_text(cert)
    Path('/etc/waggle/key.pem').write_text(key)
    Path('/etc/waggle/reverse_ssh_port').write_text(port)

    logging.info('registration complete')


def main():
    while True:
        register_if_needed()
        time.sleep(300)


if __name__ == '__main__':
    main()
