# Waggle Node Software

## Running a test environment

### Requirements

* [Docker](https://docs.docker.com/install/)
* [Docker Compose](https://docs.docker.com/compose/install/) (Included with Docker Desktop for Mac / Windows)
* Python 3

### Configuration

The node configuration can be found in `waggle-node.env`. A typical configuration specifies a node ID and a beehive hostname.

```bash
WAGGLE_NODE_ID=0000000000000001
WAGGLE_SUB_ID=0000000000000000
WAGGLE_BEEHIVE_HOST=host.docker.internal
# for actual deployment specify real hostname
# WAGGLE_BEEHIVE_HOST=beehive1.mcs.anl.gov
```

### Registration

If you have a registration key, it should be placed in `private/register.pem` and have `0600` permissions.

If you do not have a registration key, registration will fall back to directly querying a cert server. This behavior is generally only intended for local development when running a beehive server and node test environment on the same machine.

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
