# Waggle Node Application Stack

This repo contains the software components needed to run Waggle plugins and publish data
to a Beehive server. It is built on top of Docker which allows it to run on a variety
of platforms.

## Architecture Overview

```txt
┌──────────────┐┌──────────┐┌──────────┐┌───────────┐    ┆    ┌────────────────┐
│ Registration ││ Plugin 1 ││ Plugin 2 ││ Messaging │ <──┆──> │ Beehive Server │
└──────────────┘└──────────┘└──────────┘└───────────┘    ┆    └────────────────┘
            ↑ Waggle Node Application Stack ↑            ┆
┌───────────────────────────────────────────────────┐    ┆
│                     Docker                        │    ┆
└───────────────────────────────────────────────────┘    ┆
```

## Requirements

* [Docker](https://docs.docker.com/install/)
* [Docker Compose](https://docs.docker.com/compose/install/) (Included with Docker Desktop for Mac / Windows)
* Python 3

## Specifying a Beehive Server

The easiest way to get a complete environment running for development is to deploy a local [beehive](https://github.com/waggle-sensor/beehive-server) on the same machine as the node stack. Please refer to the [README](https://github.com/waggle-sensor/beehive-server/blob/master/README.md) to learn more.

In order to complete the end-to-end data pipeline, virtual waggle must register with a beehive server. For guidance, please read either the single machine deployment or remote beehive deploy steps below.

### Registration - Single Machine Option

If you are developing entirely on a single machine, then you'll need to generate a registration key pair _before_ deploying beehive. First, go to the directory you cloned `beehive-server` and run:

```sh
ssh-keygen -f ssh/id_rsa_waggle_aot_registration -N ''
```

Copy the `ssh/id_rsa_waggle_aot_registration` file to your virtual waggle directory at `private/register.pem` with `0600` permissions.

You are now ready to deploy beehive and virtual waggle together.

### Registration - Remove Beehive Option

If you are developing against a remote beehive server, you will need to request a registration key from the beehive-server admin and add it to `private/register.pem` with `0600` permissions. Please remember the hostname of this beehive server for use in the Configuration step later.

## Running Node Application Stack

### Configuration

The node configuration can be found in `waggle-node.env`. A typical configuration specifies a node ID and a beehive hostname.

```bash
WAGGLE_NODE_ID=0000000000000001
WAGGLE_SUB_ID=0000000000000000

# For single machine option on Docker Desktop for Mac / Windows, please use:
WAGGLE_BEEHIVE_HOST=host.docker.internal

# For single machine option on Linux, please use the IP address, please use:
WAGGLE_BEEHIVE_HOST=172.17.0.1

# For remote beehive option, please use the remote hostname:
WAGGLE_BEEHIVE_HOST=beehive1.mcs.anl.gov
```

Known Issue: We are working on a solution to unify the Docker Desktop and Docker on Linux configurations for single machine deployments. On Linux, we are explicitly required to set WAGGLE_BEEHIVE_HOST to the Docker network bridge IP address. This can be found using `docker network inspect bridge | grep Gateway`.

### Running the Node Environment

To start the node environment, run:

```sh
./waggle-node up
```

To stop the node environment, run:

```sh
./waggle-node down
```

To view logs from the node environment, you can use:

```sh
# view all logs, including node system services
./waggle-node logs

# view logs from just plugins
./waggle-node logs | awk '$1 ~ /plugin/'
```

### Runnning Plugins

Assuming you've already started a node environment, plugins can be run using:

```sh
./waggle-node run path/to/plugin1 path/to/plugin2 ...
```

This will rebuild and run each plugin, then attach to the logs.
