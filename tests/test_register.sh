#!/bin/bash

cd $(dirname $0)/..

./virtual-waggle down
rm private/*.pem reverse_ssh_port
./virtual-waggle up

for attempt in $(seq 3); do
    echo "waiting for credentials. attempt $attempt / 3"
    sleep 5
    if test -e private/cacert.pem && test -e private/cert.pem && test -e private/key.pem; then
        echo "got credentials"
        exit 0
    fi
done

echo "failed to get credentials"
exit 1
