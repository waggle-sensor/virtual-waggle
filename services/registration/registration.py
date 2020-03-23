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


should_exist = [
    Path('/etc/waggle/cacert.pem'),
    Path('/etc/waggle/cert.pem'),
    Path('/etc/waggle/key.pem'),
    Path('/etc/waggle/reverse_ssh_port'),
]


def get_cacert_from_local_cert_server():
    r = requests.get(f'http://{WAGGLE_BEEHIVE_HOST}:24181/certca')
    r.raise_for_status()
    return scan_certificate(r.text)


def get_credentials_from_local_cert_server():
    r = requests.get(
        f'http://{WAGGLE_BEEHIVE_HOST}:24181/node?{WAGGLE_NODE_ID}')
    r.raise_for_status()
    return r.text


def register_with_local_cert_server():
    cacert = get_cacert_from_local_cert_server()
    logging.info('got ca cert')

    response = get_credentials_from_local_cert_server()
    cert = scan_certificate(response)
    key = scan_key(response)
    port = scan_port(response)
    logging.info('got credentials')

    Path('/etc/waggle/cacert.pem').write_text(cacert)
    Path('/etc/waggle/cert.pem').write_text(cert)
    Path('/etc/waggle/key.pem').write_text(key)
    Path('/etc/waggle/reverse_ssh_port').write_text(port)


def register_if_needed():
    # TODO check if credentials are valid
    if all(path.exists() for path in should_exist):
        logging.info('credentials already exist. done!')
        return

    logging.info('registering node %s on beehive %s',
                 WAGGLE_NODE_ID, WAGGLE_BEEHIVE_HOST)

    # TODO add support for using registration key
    logging.warning('no registration key. falling back to local cert server.')
    register_with_local_cert_server()
    logging.info('registration complete')


def main():
    while True:
        register_if_needed()
        time.sleep(300)


if __name__ == '__main__':
    main()
