#!/bin/bash

docker-compose $(ls docker-compose*yml | awk '{printf "-f %s ", $0}') logs -f $@
