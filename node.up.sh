#!/bin/bash

docker-compose $(ls docker-compose*yml | awk '{printf "-f %s ", $0}') up --build -d --remove-orphans

while ! python3 shovelctl.py enable; do
    sleep 3
done
