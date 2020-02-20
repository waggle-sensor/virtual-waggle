arch = $(shell uname -p)
name = message-staging
image = waggle/$(name):0.1.0-node-$(arch)
include ../Makefile.service

deploy:
	-cat $(EDGE_ROOT)/etc/waggle/node_id
	docker run \
		--detach \
		--net $(EDGE_DOCKER_NETWORK) \
		-v $(EDGE_ROOT)/etc/waggle:/etc/waggle:ro \
		--restart=always \
		--name $(name) \
		$(image)
