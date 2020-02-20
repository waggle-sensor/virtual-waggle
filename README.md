# Waggle Node Software

## Running a test environment

Scratch space for debugging RabbitMQ shovels and trying data stack spin up.

### Configuration

The node configuration can be found in `waggle-node.env`. A typical configuration specifies a node ID and a beehive hostname.

```text
WAGGLE_NODE_ID=0000000000000001
WAGGLE_BEEHIVE_HOST=host.docker.internal
```

### Commands

To start the node environment, run:

```sh
./node.up.sh
```

To stop the node environment, run:

```sh
./node.down.sh
```

To view logs from the node environment, run:

```sh
./node.logs.sh
```
