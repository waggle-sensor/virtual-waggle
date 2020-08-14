#!/bin/bash -e

cd $(dirname $0)/..

rm -rf plugin-test
./waggle-node newplugin test
./waggle-node build plugin-test
rm -rf plugin-test
