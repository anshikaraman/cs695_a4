# cs695_a4

## Assignment 4: Implementing a load balancer

### Team Members
- Anshika Raman (210050014)
- Aman Sharma (210100011)

### Prerequisites
1. Make sure Docker engine is installed on the system and is running. If not, follow the instructions [here](https://docs.docker.com/engine/install/). Check the status of the Docker engine using the following command:
    ```
    sudo systemctl status docker
    ```
    - The output should show `active (running)` status of the Docker engine.
    - Make sure the Docker context is available and is set to the desired context. If not, set the context using the following command:
        ```
        docker context ls
        docker context use default
        ```
    - The asterisk (*) symbol indicates the current context being used.

2. We have used the [HTTP load generator](https://github.com/rickydebojeet/http-load-generator) designed by Debojeet Das. This tool is used to generate HTTP requests to the gateway. It creates multiple threads, one for each user, and sends requests to the gateway. The gateway then forwards the requests to the replicas of the backend services based on the policy chosen. We modified this tool in order to ensure that the requests being generated from each user or thread uses a unique port number. This is done to ensure that the gateway can distinguish between the requests coming from different users. The modified code can be found in the fork of the original repository [here](https://github.com/amansharma612/http-load-generator). Clone this repository in order to replicate our working setup.

### Instructions to run the code
1. Run the following command to start the conductor (an admin managing the load balancer) with the certain options. Following are the available options:
    ```
    python3 conductor.py -h
    ```
    - The options are:
        | Option | Description |
        | --- | --- |
        | `--phys-machine` | IP address of the physical machine, multiple machines can be specified |
        | `--usernames` | Usernames of the physical machines, multiple usernames can be specified |
        | `--port` | Port number to run the gateway service, multiple port numbers can be specified |
        | `--replicas` | Number of replicas to start, multiple numbers can be specified |
        | `--policy` | Load balancing policy to use, one of `ROUND_ROBIN` and `LEAST_RESPONSE_TIME`, default is `ROUND_ROBIN` |
        | `-h` or `--help` | Show the help message and exit |
    - Example command:
        ```
        python3 conductor.py --phys-machine 10.42.0.219 --usernames anshikaaramann --port 9000 --replicas 3
        ```
        - This command will start the conductor on the physical machine with IP address `10.42.0.219` and username `anshikaaramann`. The backend services will be bind with the host machine's port starting from `9000` and `3` replicas of the backend services will be created. The load balancing policy used will be `ROUND_ROBIN`.
    - The conductor will first start the gateway service on the port number `8000` of the machine where the above command is ran and then start the backend services on the specified physical machines using Docker context.
    - Once all the backend services are started, the conductor will register the replicas with the gateway with their respective IP addresses and port numbers. This information is used by the gateway to forward the requests to the replicas based on the load balancing policy chosen.

2. The gateway will listen for the incoming requests on port `8000` and forward them to the replicas based on the load balancing policy chosen.

3. If the policy chosen is `ROUND_ROBIN`, the gateway will forward the requests to the replicas in a round-robin fashion.

4. If the policy chosen is `LEAST_RESPONSE_TIME`, the gateway will keep track of the response times of the replicas for the last `n` requests, this `n` is nothing but the `WINDOW_SIZE` and is set to `3` by default in the gateway. The gateway first employs the round-robin policy to forward the requests to the replicas. Once the response times of the replicas for the last `WINDOW_SIZE` requests are available, the gateway will forward the next request to the replica with the least response time by computing the average response time of the replicas for the last `WINDOW_SIZE` requests.

5. One can generate the HTTP requests using the http-load-generator tool (modified version) mentioned in the prerequisites. The tool has some macros defined in the `http_client.hh` that needs to be set before running the tool. These are:
    - `HOST`: The host to send requests to.
    - `URL`: The URL to send requests to.
    - `PORT`: The port to send requests to.
    - `SANITY_CHECK`: The expected response head.
    - `OUTPUT`: The expected response body.
    - `FAULT_EXIT`: 0 for tolerant, 1 for strict.

6. After this, the following variables can be changed from their default values in the `run_genearator.sh` script:
    - `USER_COUNT:` The number of users to simulate.
    - `THINK_TIME:` The think time between requests.
    - `TEST_DURATION:` The duration of the test in seconds.
    - `CPU:` The CPU to run the load generator on.

    > CPU is the CPU number, not the CPU name. You can find the CPU number by running `lscpu`.

7. Run the following command to start the load generator:
    ```
    bash run_generator.sh
    ```
    - This will start the load generator with the specified number of users and the duration of the test.
    - The logs for each user can be found in the newly created `results` directory of the load generator tool, with the name `<user_number>_load_gen.log`.
    - The file `results/results.dat` will contain the throughput (requests per second) and the average response time (in ms) for each load level i.e. the number of users.
    - The file `results/results.png` will contain the graph of the throughput and the average response time for each load level.

8. One can look into the working of the gateway (or load balancing) service by attaching its container using the following command:
    ```
    docker --context default attach gateway
    ```
    - This will show the logs of the gateway service.

9. The conductor provides with certain options, a user can choose from. They are as follows:
    - 1. Stop all the services and exit: This option will stop all the services running on the physical machines and the gateway service and exit. It will switch to the respective context and stop the replicas.
    - 2. Kill a replica: This option will kill a replica of the backend service. The user will be asked to enter the replica name to kill, which is in the format: `<phys_machine_username>-backend<replica_number>`. The replicas are named in this format to distinguish between the replicas running on different physical machines. It will automatically switch to the respective context and kill the replica. It will also deregister the replica from the gateway.
    - 3. Start a replica: This option will start a replica of the backend service. The user will be asked to enter the physical machine IP address, username, port number, and the replicas to start. It will automatically switch to the respective context and start the replica. It will also register the replica with the gateway.

10. In case the conductor is stopped abruptly or the replicas are not stopped properly, the user can run the following command to stop all the services and exit:
    ```
    docker context use <context-name>
    bash stop_containers.sh
    ```
    - This will stop all the services running on the physical machines associated with the context.

### Directory Structure
- `conductor.py`: The conductor script that manages the load balancer. It starts the gateway service and the backend services on the physical machines using Docker context. It registers the replicas with the gateway and provides options to stop the services, kill a replica, and start a replica.
- `gateway/gateway.py`: The gateway script that listens for the incoming requests and forwards them to the replicas based on the load balancing policy chosen.
- `backend/backend.py`: The backend script that simulates the backend service. It receives the requests from the gateway and sends the response back to the gateway.
- `results/`: The directory that contains the plots generated by the load generator tool.
- `stop_containers.sh`: The script that stops all the services running associated with the context currently being used.
- `project_report.pdf`: The project report that contains the detailed explanation of the assignment.

### Load Balancing Policies
1. **Round Robin**: The gateway forwards the requests to the replicas in a round-robin fashion.
2. **Least Response Time**: The gateway keeps track of the response times of the replicas for the last `n` requests, where `n` is the `WINDOW_SIZE` and is set to `3` by default in the gateway. The gateway first employs the round-robin policy to forward the requests to the replicas. Once the response times of the replicas for the last `WINDOW_SIZE` requests are available, the gateway forwards the next request to the replica with the least response time by computing the average response time of the replicas for the last `WINDOW_SIZE` requests.

### Contributions
- Anshika Raman:
    - Implemented the conductor script that manages the load balancer. It starts the gateway service and the backend services on the physical machines using Docker context. It registers the replicas with the gateway and provides options to stop the services, kill a replica, and start a replica.
    - Implemented the backend script that simulates the backend service. It receives the requests from the gateway and sends the response back to the gateway.
    - Implemented the least response time policy in the gateway script. It keeps track of the response times of the replicas for the last `n` requests and forwards the next request to the replica with the least response time.
    - Wrote the README.md file, created the the presentation.
- Aman Sharma:
    - Modified the http-load-generator tool to ensure that the requests being generated from each user or thread uses a unique port number. This is done to ensure that the gateway can distinguish between the requests coming from different users.
    - Created the plots for the throughput and the average response time for each load level using the results obtained from the load generator tool.
    - Created the project report.

### References
1. [HTTP load generator](http://github.com/aman612/http-load-generator)
2. [Docker Context documentation](https://docs.docker.com/engine/context/working-with-contexts/)

### Credits
- We would like to thank Debojeet Das for providing the HTTP load generator tool and his guidance. We would also like to thank Prof. Purushottam Kulkarni for guiding us throughout the assignment.
