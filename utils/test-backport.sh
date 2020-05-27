#!/bin/bash
# TODO add restart policy

hostname=node50288

# rsync -av /Users/sean/waggle-node/services/rabbitmq-node/ $hostname:/wagglerw/rabbitmq-node/
# ssh $hostname docker build -t waggle/rabbitmq:nc /wagglerw/rabbitmq-node/

ssh $hostname bash -c '
docker pull waggle/rabbitmq:nc
docker pull waggle/shovelctl
docker pull waggle/plugin-metsense:4.1.0

docker rm -f rabbitmq

echo "starting rabbitmq permissions"
docker run -d --restart always --network waggle \
    -v /etc/waggle/cacert.pem:/run/waggle/cacert.pem:ro \
    -v /etc/waggle/cert.pem:/run/waggle/cert.pem:ro \
    -v /etc/waggle/key.pem:/run/waggle/key.pem:ro \
    --name rabbitmq \
    waggle/rabbitmq:nc

echo "fixing credential permissions"
docker exec -i --user root rabbitmq bash -c "mkdir -p /etc/waggle; cp /run/waggle/* /etc/waggle/; chown -R rabbitmq:rabbitmq /etc/waggle"

echo "setting up shovels"
docker run -i --network waggle --rm -e WAGGLE_NODE_ID=0000001e06118459 -e WAGGLE_SUB_ID=0000000000000000 -e WAGGLE_BEEHIVE_HOST=140.221.47.67 waggle/shovelctl enable

echo "starting metsense plugin"
docker rm -f plugin-metsense
docker run -d --restart always --network waggle --device /dev/waggle_coresense --name plugin-metsense waggle/plugin-metsense:4.1.0
'
