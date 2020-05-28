#!/bin/bash

# TODO organize node info into waggle-node.env like in virtual waggle
# TODO look at using docker-compose even on the node
# TODO handle auth related to plugins

hostname=edge50288

ssh $hostname bash -c '
docker pull waggle/rabbitmq:ep
docker pull waggle/plugin-media-streaming:0.1.0
docker pull waggle/plugin-carped:1.0.0

docker network create waggle

docker rm -f rabbitmq cam_bottom_live waggle-plugin-carped

docker run -d --restart always --network waggle \
    -p 5672:5672 \
    --name rabbitmq \
    waggle/rabbitmq:ep

docker run -d \
  --restart always \
  --network waggle \
  --device /dev/waggle_cam_bottom \
  --name cam_bottom_live \
  waggle/plugin-media-streaming:0.1.0 \
  -f v4l2 \
  -input_format mjpeg \
  -video_size 640*480 \
  -i /dev/waggle_cam_bottom \
  -c:v libx264


while ! docker exec -it rabbitmq rabbitmqctl add_user "plugin-50-1.0.0-0" "worker"; do
  sleep 3
done

docker exec -it rabbitmq rabbitmqctl set_permissions "plugin-50-1.0.0-0" ".*" ".*" ".*"

docker run -d \
  --restart always \
  --network waggle \
  --name waggle-plugin-carped \
  -e WAGGLE_NODE_ID=0000001e06118459 \
  -e WAGGLE_SUB_ID=0000000000000001 \
  -e WAGGLE_PLUGIN_HOST=rabbitmq \
  -e WAGGLE_PLUGIN_ID=50 \
  -e WAGGLE_PLUGIN_VERSION=1.0.0 \
  -e WAGGLE_PLUGIN_INSTANCE=0 \
  -e WAGGLE_PLUGIN_USERNAME=plugin-50-1.0.0-0 \
  -e WAGGLE_PLUGIN_PASSWORD=worker \
  waggle/plugin-carped:1.0.0
'

# todo: just predefine the plugin user for the aot nodes...
# we'll work out the final configuration approach later...
# error: carped produces messages too fast!!!
# error: missing user ID
