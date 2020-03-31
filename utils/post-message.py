import requests
import json
from base64 import b64encode
import waggle.protocol

with requests.Session() as session:
    session.auth = ('admin', 'admin')

    r = session.post('http://localhost:15673/api/exchanges/%2f/messages/publish', json={
        'properties': {},
        'routing_key': '0000000000000001.0000000000000000.ansible',
        'payload': b64encode(b'testing').decode(),
        'payload_encoding': 'base64',
    })

    print(r.text)

    r = session.post('http://localhost:15673/api/exchanges/%2f/messages/publish', json={
        'properties': {},
        'routing_key': '0000000000000001.0000000000000000.plugin.37.0.1.0.0',
        'payload': b64encode(b'hello').decode(),
        'payload_encoding': 'base64',
    })

    print(r.text)
