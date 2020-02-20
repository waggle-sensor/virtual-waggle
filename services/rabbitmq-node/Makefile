arch = $(shell uname -p)
name = rabbitmq
image = waggle/$(name):3.8.0-node-$(arch)
include ../Makefile.service

deploy:
	-docker network create $(EDGE_DOCKER_NETWORK)
	-docker rm -f $(name)
	docker run \
		--detach \
		--network $(EDGE_DOCKER_NETWORK) \
		--restart=always \
		-e RABBITMQ_NODENAME=rabbitmq \
		-v $(EDGE_ROOT)/rabbitmq/:/var/lib/rabbitmq/:rw \
		-v $(EDGE_ROOT)/log/rabbitmq/:/var/log/rabbitmq/:rw \
                -v $(EDGE_ROOT)/certs:/etc/waggle/certs:ro \
		-p 15672:15672 \
		--hostname rabbitmq \
		--network-alias rabbitmq \
		--name $(name) \
		$(image)
