#!/bin/bash
#
# CS695 Conductor that manages containers
# Author: <your-name>
#
# echo -e "\e[1;32mCS695 Conductor that manages containers\e[0m"

set -o errexit
set -o nounset
umask 077


############## utility function start

die()
{
    echo "$1" >&2
    exit 1
}

build()
{
    local IMG_NAME=${1:-}
    local TAG_NAME=${2:-}
    local DOCKERFILE_PATH=${3:-}

    if [ -z "$DOCKERFILE_PATH" ]; then
        docker pull $IMG_NAME:$TAG_NAME
    else
        docker build -t $IMG_NAME:$TAG_NAME $DOCKERFILE_PATH || die "Failed to build image $IMAGE"
    fi

}

# This function shows all downloaded container images that are kept in .images directory
images()
{
    docker images
}

# This function deletes a container image
remove_image()
{
    local IMG_NAME=${1:-}
    local TAG_NAME=${2:-}

    [ -z "$IMG_NAME" ] && die "Image name is required"

    docker image rm --force $IMG_NAME:$TAG_NAME
    if [ $? -eq 0 ]; then
        echo -e "\e[1;32m$IMG_NAME successfully removed\e[0m"
    else
        die "Failed to remove $IMG_NAME"
    fi
}

run()
{
    local IMAGE=${1:-}
    local TAG=${2:-}
    local NAME=${3:-}

    [ -z "$NAME" ] && die "Container name is required"
    [ -z "$IMAGE" ] && die "Image name is required"

    shift 3

    if [ "$EXPOSE" -eq "1" ]; then
        # Lesson: This iptable rule will replace the ip address and port of any TCP packet received on default interface
        # destined to OUTER_PORT
        # iptables -t nat -A PREROUTING -p tcp -i ${DEFAULT_IFC} --dport ${OUTER_PORT} -j DNAT --to-destination ${INSIDE_IP4}:${INNER_PORT}
        # Lesson: The above rule will only route packets received on the external interface. As a result
        # curl <host-self-ip>:port will not work within the host itself.
        # This iptable rule wiill redirect packets generated
        # within the host with destination set as hostip:OUTER_PORT to the containers:INNER_PORT.
        # This will still not work for localhost/127.0.0.1. You will have to send using the host-ip
        # iptables -t nat -A OUTPUT -o lo -m addrtype --src-type LOCAL --dst-type LOCAL -p tcp --dport ${OUTER_PORT} -j DNAT --to-destination ${INSIDE_IP4}:${INNER_PORT}
        # Lesson: Allows forwarding of TCP session initiator packets from the public to the container
        # iptables -A FORWARD -p tcp -d ${INSIDE_IP4} --dport ${INNER_PORT} -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT
       docker run -d -i -p ${INNER_PORT}:${OUTER_PORT} --name "$NAME" "$IMAGE:$TAG"
    else
       docker run -d -i --name "$NAME" "$IMAGE:$TAG"
    fi

}

# This will show containers that are currently running
show_containers()
{
    docker ps -a
}


# This function will stop a running container
# To stop a container you need to kill the entry process within the container
# You should also unmount any mount points you created while running the container
stop()
{
    local NAME=${1:-}

    [ -z "$NAME" ] && die "Container name is required"

    docker stop $NAME
    docker container rm --force $NAME
    echo -e "\e[1;32m$NAME succesfully removed\e[0m"
}

# Subtask 3.b
# This function will execute a program within a running container
exec()
{
    local NAME=${1:-}
    local CMD=${2:-}

    [ -z "$NAME" ] && die "Container name is required"

    shift # shift arguments so that remaining arguments represent the program and its arguments to execute

    # if no command is given then substitute with /bin/sh
    local EXEC_CMD_ARGS=${@:-/bin/sh}

    echo -e "\e[1;32mExecuting $CMD in $NAME container!\e[0m"
    docker exec -t $NAME $EXEC_CMD_ARGS
}


# This function is used to enable peer to peer packet traffic between two containers
peer()
{
    local NAMEA=${1:-}
    local NAMEB=${2:-}
    [ -z "$NAMEA" ] && die "First Container name is required"
    [ -z "$NAMEB" ] && die "Second Container name is required"

    # create a bridge network
    docker network create -d bridge "bridge-${NAMEA}-${NAMEB}"

    # connect the running containers with this bridge
    docker network connect "bridge-${NAMEA}-${NAMEB}" ${NAMEA}
    docker network connect "bridge-${NAMEA}-${NAMEB}" ${NAMEB}
}


usage()
{
    local FULL=${1:-}

    echo "Usage: $0 <command> [params] [options] [params]"
    echo ""
    echo "Commands:"
    echo "build <img> <tag> <dockerfile>        Build image for containers"
    echo "images                                List available images"
    echo "rmi <img>                             Delete image"
    echo "run <img> <cntr> -- [command <args>]  Runs [command] within a new container named <cntr> fron the image named <img>"
    echo "                                      if no command is given it will run /bin/sh by default"
    echo "ps                                    Show all running containers"
    echo "stop <cntr>                           Stop and delete container"
    echo "exec <cntr> -- [command <args>]       Execute command (default /bin/sh) in a container"
    echo "peer <cntr> <cntr>                    Allow to container to communicate with each other"
    echo ""

    if [ -z "$FULL" ] ; then
        echo "Use --help to see the list of options."
        exit 1
    fi

    echo "Options:"
    echo "-h, --help                Show this usage text"
    echo ""
    echo ""
    echo ""
    echo "-e, --expose <inner-port>-<outer-port>"
    echo "                          Expose some port of container (inner)"
    echo "                          as the host's port (outter)"
    echo ""
    echo ""
    exit 1
}

OPTS="he:"
LONGOPTS="help,expose:"

OPTIONS=$(getopt -o "$OPTS" --long "$LONGOPTS" -- "$@")
[ "$?" -ne "0" ] && usage >&2 || true

eval set -- "$OPTIONS"

while true; do
    arg="$1"
    shift
    case "$arg" in
        -h | --help)
            usage full >&2
            ;;
        -e | --expose)
            PORT="$1"
            INNER_PORT=${PORT%-*}
            OUTER_PORT=${PORT#*-}
            EXPOSE=1
            shift
            ;;
        -- )
            break
            ;;
    esac
done

[ "$#" -eq 0 ] && usage >&2

case "$1" in
    build)
        CMD=build
        ;;
    images)
        CMD=images
        ;;
    rmi)
        CMD=remove_image
        ;;
    run)
        CMD=run
        ;;
    ps)
        CMD=show_containers
        ;;
    stop)
        CMD=stop
        ;;
    exec)
        CMD=exec
        ;;
    peer)
        CMD=peer
        ;;
    "help")
        usage full >&2
        ;;
    *)
        usage >&2
        ;;
esac

shift
$CMD "$@"



