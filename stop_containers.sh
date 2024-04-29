#!/bin/bash

# args=("$@")
# for i in "${args[@]}"; do
#     docker stop $i
#     docker container rm --force $i
# done

docker stop $(docker ps -a -q)
docker container rm --force $(docker ps -a -q)
