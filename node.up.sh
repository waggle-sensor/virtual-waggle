#!/bin/bash

if [ -e 'docker-compose.plugins.yml' ]; then
    compose_file_args='-f docker-compose.system.yml -f docker-compose.plugins.yml'
else
    compose_file_args='-f docker-compose.system.yml'
fi

command_up() {
    docker-compose $compose_file_args up --build -d --remove-orphans

    while ! python3 shovelctl.py enable; do
        sleep 3
    done
}

command_down() {
    docker-compose $compose_file_args down --remove-orphans
}

command_logs() {
    docker-compose $compose_file_args logs -f
}

command="$1"
shift

case "$command" in
    up) command_up $@ ;;
    down) command_down $@ ;;
    logs) command_logs $@ ;;
esac
