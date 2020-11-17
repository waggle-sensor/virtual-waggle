#!/bin/bash -e

cd $(dirname $0)/..

rm -rf plugin-test
./virtual-waggle newplugin test
./virtual-waggle build plugin-test
rm -rf plugin-test
