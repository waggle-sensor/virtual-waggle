#!/bin/bash -e

rm -rf plugin-test
../waggle-node newplugin test
../waggle-node build plugin-test
rm -rf plugin-test
