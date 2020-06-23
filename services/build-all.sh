#!/bin/bash

build_service() {
    docker buildx build -t "$1" --platform linux/amd64,linux/arm64,linux/arm/v7 --push "$2"
}

build_service waggle/media-server media-server
build_service waggle/rabbitmq:nc rabbitmq-nc
build_service waggle/rabbitmq:ep rabbitmq-ep
build_service waggle/stage-messages stage-messages
build_service waggle/shovelctl shovelctl
build_service waggle/registration registration
