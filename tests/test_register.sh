#!/bin/bash

cd ..

./waggle-node down
rm private/*.pem reverse_ssh_port
./waggle-node up

for attempt in $(seq 3); do
    echo "waiting for credentials. attempt $attempt / 3"
    sleep 5
    if test -e private/cacert.pem && test -e private/cert.pem && test -e private/key.pem; then
        exit 0
    fi
done

echo "failed to get credentials"
exit 1
