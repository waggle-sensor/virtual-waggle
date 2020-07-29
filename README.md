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
* Python 3.6 and above

## Specifying a Beehive Server (Optional)

Virtual Waggle can run without connecting to a Beehive Server. If you only want to work on plugins, you can skip ahead to "Setting up Virtual Waggle Environment".

The easiest way to get a complete environment running for development is to deploy a local [beehive](https://github.com/waggle-sensor/beehive-server) on the same machine as the node stack. Please refer to the [README](https://github.com/waggle-sensor/beehive-server/blob/master/README.md) to learn more.

In order to complete the end-to-end data pipeline, virtual waggle must register with a beehive server. For guidance, please read either the single machine deployment or remote beehive deploy steps below.

### Registration - Single Machine Option

If you are developing entirely on a single machine, then you'll need to generate a registration key pair _before_ deploying beehive. First, go to the directory you cloned `beehive-server` and run:

```sh
# remove all stale keys
rm ssh/id_rsa_waggle_aot_registration*
ssh-keygen -f ssh/id_rsa_waggle_aot_registration -N ''
```

Copy the `ssh/id_rsa_waggle_aot_registration` file to your virtual waggle directory at `private/register.pem` with `0600` permissions.

You are now ready to deploy beehive and virtual waggle together.

### Registration - Remote Beehive Option

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

### Setting up Virtual Waggle Environment

In order to run plugins, you need to ensure all the Virtual Waggle environment is running. To do this, run:

```sh
./waggle-node up
```

When you're done, you can cleanup the Virtual Waggle environment by running:

```sh
./waggle-node down
```

### Building and Running Plugins

Once you've run `./waggle-node up`, you're ready to start working on plugins using the `build` and `run` commands:

* The `build` command accepts a plugin directory and outputs the name of the plugin that was built.

* The `run` command accepts a plugin and runs it inside the Virutal Waggle environment.

In a typical development process, you'll combine these to build and run a plugin as follows:

```sh
./waggle-node run $(./waggle-node build path/to/plugin)
```

As a concrete example, if I want to clone the edge plugins repo and try out the simple plugin:

```sh
git clone https://github.com/waggle-sensor/edge-plugins
./waggle-node run $(./waggle-node build ./edge-plugins/plugin-simple)
```

```sh
Sending build context to Docker daemon  9.728kB
Step 1/9 : FROM waggle/plugin-base:0.1.0
 ---> ea69e837abcc
Step 2/9 : COPY /plugin/requirements.txt /plugin/requirements.txt
 ---> Using cache
 ---> 935d669532c1
Step 3/9 : RUN pip3 install -r /plugin/requirements.txt
 ---> Using cache
 ---> 9bb4fbe7af74
Step 4/9 : COPY /plugin /plugin
 ---> Using cache
 ---> afde4ca6c137
Step 5/9 : WORKDIR /plugin/plugin_bin
 ---> Using cache
 ---> a4fb92940ba3
Step 6/9 : CMD ["./plugin_node"]
 ---> Using cache
 ---> 2cddfae8e4ae
Step 7/9 : LABEL waggle.plugin.id=100
 ---> Using cache
 ---> 91793681c0df
Step 8/9 : LABEL waggle.plugin.name=simple
 ---> Using cache
 ---> 1df87a316682
Step 9/9 : LABEL waggle.plugin.version=0.2.0
 ---> Using cache
 ---> a69156c63abb
Successfully built a69156c63abb
Successfully tagged plugin-simple:0.2.0
Setting up plugin-simple:0.2.0
Running plugin-simple:0.2.0

adding measurement 0.946405801897217
adding measurement 0.7775963052387123
adding measurement 0.41189924821227397
adding measurement 0.3047326389740709
adding measurement 0.006611365595469376
...
```

You can also run remote plugins from the ECR with `run`. For example:

```sh
./waggle-node run waggle/plugin-simple:0.2.0
```

### Creating a New Plugin

A new plugin outline can be generated using the `newplugin` command as follows:

```sh
./waggle-node newplugin name
```

This will create a plugin directory named `plugin-name` which will contain:

* plugin.py - main code file
* requirements.txt - python dependencies
* Dockerfile - build steps
* sage.json - metadata file

Going back to the section, this can be built and run using:

```sh
./waggle-node run $(./waggle-node build plugin-name)
```

### Playback Service (Optional)

Virtual waggle runs an instance of the [playback server](https://github.com/waggle-sensor/playback-server). The server is configured to use `playback/` as the root image and video directory and is available inside VW using thee hostname `playback`.

Specifically, you can add media to:

```txt
playback/
  bottom/
    live.mp4        <- bottom camera video
    images/         <- bottom camera images
      image1.jpg
      image2.jpg
      ...
  top/
    live.mp4        <- top camera video
    images/         <- top camera images
      image1.jpg
      image2.jpg
      ...
```

These are available over the endpoints:

```txt
# serves mp4 video stream
http://playback:8090/bottom/live.mp4
http://playback:8090/top/live.mp4

# serves sequence of images from data directory
http://playback:8090/bottom/image.jpg
http://playback:8090/top/image.jpg
```

The playback server also provides two additional endpoints to aid debugging. These are
always available and don't require you to add images or videos in order to use them.

```txt
# solid black image
http://playback:8090/blank.jpg

# random noise image
http://playback:8090/noise.jpg
```

### Debugging (Optional)

The `report` command can be used to quickly get some internal status of VW. For now, this provides:

* Status of RabbitMQ Queues
* Status of RabbitMQ Shovels
