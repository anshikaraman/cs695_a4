# cs695_a4

## Aman -- 26/04/24

1. Registering IP of Host instead of container's IP address using /register route. Edit the IP address so that it matches with your host.

2. profiler(): sends a request to the Docker engine API for getting stats for each running container. Runs in a separate thread inside the gateway ( TODO : Guard the cpu_util dict usage using locks inside the gateway)

3. Added a dummy CPU workload inside the service