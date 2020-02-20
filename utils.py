from pathlib import Path
import re
import binascii


def read_username_from_cert():
    s = Path('private/cert.pem').read_text()
    match = re.search(r'-----BEGIN CERTIFICATE-----', s)
    start = match.end()
    match = re.search(r'-----END CERTIFICATE-----', s)
    end = match.start()
    data = s[start:end]
    data = binascii.a2b_base64(data)
    match = re.search(b'node-.{16}', data)
    return match.group().decode()
