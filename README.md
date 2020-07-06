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

# for local beehive, please use:
WAGGLE_BEEHIVE_HOST=host.docker.internal

# for remote beehive, please use the hostname:
# WAGGLE_BEEHIVE_HOST=beehive1.mcs.anl.gov
```

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

# view plugin related logs
./waggle-node logs | grep plugin
```

### Building Plugins

To rebuild a plugin locally, you can run:

```sh
docker build -t waggle/plugin-simple:0.1.0 path/to/plugin-simple
```

where `waggle/plugin-simple:0.1.0` is the `organization/name:version` of my
plugin and `path/to/plugin-simple` is the directory it lives in.

### Publishing Plugins (Optional, Experimental)

_This is under major development until the Sage ECR is in place. For now, we are using Dockerhub directly._

_We we doing a multi-arch build here which requires using Docker experimental features._

```sh
docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 --push -t waggle/plugin-simple-detector:0.1.0 path/to/plugin-simple
```

### Scheduling Plugins

_This is under major development! It will eventually be handled by our resource manager, but for now we have some manual tools to handle this._

_Additionally, it's likely that plugins will eventually be kept in the [ECR](https://github.com/sagecontinuum/ecr) and available across platforms. For now, when testing on my laptop I've had to manually build docker images from the [edge-plugins](https://github.com/waggle-sensor/edge-plugins) repo. For now, plugins are being submitted to the [Waggle Dockerhub](https://hub.docker.com/orgs/waggle/repositories) and
[Sage Dockerhub](https://hub.docker.com/orgs/sagecontinuum/repositories)._

Assuming you've already started a node environment, we'll schedule the single plugin `waggle/plugin-simple:0.1.0`.

```sh
./waggle-node schedule waggle/plugin-simple:0.1.0
```

Now, we'll look at the logs one more time:

```sh
# view plugin related logs
./waggle-node logs | grep plugin
```
