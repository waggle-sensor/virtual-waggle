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

### Registration

If you are developing entirely on a single machine, you will _not_ need a registration key. The registration service will automatically get credentials directly from the local beehive-server. _This is primarily intended to be used for development, not a full deployment!_

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

### Scheduling Plugins

_This is under major development! It will eventually be handled by our resource manager, but for now we have some manual tools to handle this._

_Additionally, it's likely that plugins will eventually be kept in the [ECR](https://github.com/sagecontinuum/ecr) and available across platforms. For now, when testing on my laptop I've had to manually build docker images from the [edge-plugins](https://github.com/waggle-sensor/edge-plugins) repo._

Assuming you've already started a node environment, we'll schedule the single plugin `waggle/plugin-simple:0.1.0`.

```sh
./waggle-node schedule waggle/plugin-simple:0.1.0
```

Now, we'll look at the logs one more time:

```sh
# view plugin related logs
./waggle-node logs | grep plugin
```
