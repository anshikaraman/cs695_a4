# cs695_a4

## Assignment 4: Implementing a load balancer

### Team Members
- Anshika Raman (anshikaraman)
- Aman Sharma

### Instructions to run the code
1. Run the following command to start the gateway and replicas of the frontend service. The conductor will start the gateway and 4 replicas of the frontend service.
    ```
    python3 conductor.py
    ```
    - The `docker-compose ps` should show the following services running:
        ```
        cs695_a4-gateway
        cs695_a4-frontend-1
        cs695_a4-frontend-2
        cs695_a4-frontend-3
        cs695_a4-frontend-4
        ```

2. One can run the load generator using the following command (httperf or ab [apache benchmark] can be used):
    ```
    ab -n 1000 -c 10 http://localhost:8000/
    ```

3. The logs of the gateway and replicas can be seen using the following command:
    ```
    docker-compose logs -f
    ```
    - The logs will show the requests being distributed among the replicas.

4. Use the following command to stop the conductor and the services:
    ```
    bash stop_containers.sh
    ```
