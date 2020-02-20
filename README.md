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
./waggle-node up
```

To stop the node environment, run:

```sh
./waggle-node down
```

To view logs from the node environment, run:

```sh
./waggle-node logs
```

### Adding Plugins

This is under major development! It will eventually be handled by our resource manager, but for now we have some manual tools to handle this.

Additionally, it's likely that plugins will eventually be kept in the [ECR](https://github.com/sagecontinuum/ecr) and available across platforms. For now, when testing on my laptop I've had to manually build docker images from the [edge-plugins](https://github.com/waggle-sensor/edge-plugins) repo.

First, we'll assume you've already started a node environment.

Now, we'll generate a configuration file with the single plugin `waggle/plugin-simple:0.1.0`.

```sh
./waggle-node plugins waggle/plugin-simple:0.1.0
```

This will regenerate the `docker-compose.plugins.yml` file and update the running node environment.
