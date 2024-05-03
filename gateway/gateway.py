
# This script defines a Flask application that acts as a gateway to route incoming requests to different backend services.

# default imports
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
import requests

# create a FastAPI application
app = FastAPI()

# define the data model for the container details to be registered
class ContainerDetails(BaseModel):
    name: str
    ip: str
    port: int
    status: str

# local variables to store the details of the backend services
BACKEND_DTLS = {}
req_count = {}; round_robin_idx = 0
response_time = {}
avg_response_time = {}
flag_all_reqs_window = 0
min_service_name = None

# policy types
policy_types = ["ROUND_ROBIN", "LEAST_RESPONSE_TIME", "RESOURCE_BASED"]
# define the policy for load balancing
POLICY = "ROUND_ROBIN"
# window size for moving average of response time in least response time policy
WINDOW_SIZE = 3

# dictionary for statefulness
MACHINE_DTLS = {}

# define route to accept details about backend services
@app.post("/register")
def register_backend(container: ContainerDetails):
    global BACKEND_DTLS, response_time, avg_response_time

    # add the details of the backend service to the dictionary
    if container.status == "active":
        BACKEND_DTLS[container.name] = f"http://{container.ip}:{container.port}"
        # BACKEND_DTLS[container.name] = f"http://localhost:{container.port}"
        req_count[container.name] = 0
        response_time[container.name] = []
        avg_response_time[container.name] = 0
        # print(BACKEND_DTLS)

        if container.name.split("-")[0] not in MACHINE_DTLS.keys():
            MACHINE_DTLS[container.name.split("-")[0]] = []
        print(MACHINE_DTLS)

        return Response(content=f'Registered backend service "{container.name}"', status_code=201)

    elif container.status == "inactive":
        if container.name in BACKEND_DTLS:
            msg = f'Removed backend service "{container.name}"'
            del BACKEND_DTLS[container.name]
            return Response(content=msg, status_code=200)

# define a route to accept the load balancing policy
@app.post("/set-policy")
def register_balancing_policy(policy: str = "ROUND_ROBIN"):
    global POLICY
    if policy not in policy_types:
        return Response(content=f'Invalid policy type "{policy}". Available types: {", ".join(policy_types)}', status_code=400)
    else:
        POLICY = policy
        return Response(content=f'Set the load balancing policy to "{policy}"', status_code=201)

# define a route to accept incoming requests
@app.get("/")
def load_balancer(request: Request):
    global POLICY, BACKEND_DTLS, req_count, round_robin_idx, response_time, avg_response_time, min_service_name, flag_all_reqs_window

    host = request.client.host
    port = request.client.port
    # print("Host: ", host, "Port: ", port)

    # compute hash of the client IP address
    host_hash_val = hash(host)
    mod_host_hash_val = host_hash_val % len(MACHINE_DTLS)
    mach_dtls_keys = list(MACHINE_DTLS.keys())

    if host not in MACHINE_DTLS[mach_dtls_keys[mod_host_hash_val]]:
        MACHINE_DTLS[mach_dtls_keys[mod_host_hash_val]].append(host)

    MACH_BACK_DTLS = {k: v for k, v in BACKEND_DTLS.items() if k.split("-")[0] == mach_dtls_keys[mod_host_hash_val]}

    # for round-robin policy
    if POLICY == "ROUND_ROBIN":
        service_name = list(MACH_BACK_DTLS.keys())[round_robin_idx % len(MACH_BACK_DTLS)]
        service_endpoint = MACH_BACK_DTLS[service_name]
        # increment the round-robin index after selecting the service
        round_robin_idx += 1

        try:
            response = requests.get(service_endpoint)
            req_count[service_name] += 1
            return Response(content=f'Hello from the service "{service_name}"! Request count: {req_count[service_name]}', status_code=200)
        except Exception as e:
            return Response(content=f'Failed to connect to service "{service_name}": {str(e)}', status_code=500)

    # for least response time policy
    elif POLICY == "LEAST_RESPONSE_TIME":

        # print the response time and average response time for all services
        # print()
        # print(f"Request count: {req_count}")
        # print(f'Response time for all services: {response_time}')
        # print(f'Average response time for all services: {avg_response_time}')
        # print(f'Flag all: {flag_all_reqs_window}')
        # print()

        # if request_count is less than window size, then send request to all services
        if all(value == WINDOW_SIZE for value in req_count.values()) and flag_all_reqs_window == 0:
            flag_all_reqs_window = 1

        if flag_all_reqs_window:
            min_time = min(avg_response_time.values())

            for service_name, service_endpoint in MACH_BACK_DTLS.items():
                try:
                    if avg_response_time[service_name] == min_time:
                        min_service_name = service_name
                        response = requests.get(MACH_BACK_DTLS[min_service_name])
                        req_count[service_name] += 1

                        print()
                        print(f"Service name selected: {service_name}")
                        print()

                        # compute the moving average of the response time
                        elapsed_time = response.elapsed.total_seconds()
                        response_time[service_name].pop(0)
                        response_time[service_name].append(elapsed_time)
                        avg_response_time[service_name] = round(sum(response_time[service_name]) / WINDOW_SIZE, 4)

                        return Response(content=response.text, status_code=200)
                    else:
                        continue
                except Exception as e:
                    return Response(content=f'Failed to connect to service "{service_name}": {str(e)}', status_code=500)
        else:
            # if request_count is less than window size, then send request to all services in round-robin fashion
            service_name = list(MACH_BACK_DTLS.keys())[round_robin_idx % len(MACH_BACK_DTLS)]
            service_endpoint = MACH_BACK_DTLS[service_name]
            # increment the round-robin index after selecting the service
            round_robin_idx += 1

            try:
                response = requests.get(service_endpoint)
                req_count[service_name] += 1

                # compute the moving average of the response time
                elapsed_time = response.elapsed.total_seconds()
                response_time[service_name].append(elapsed_time)

                if req_count[service_name] == WINDOW_SIZE:
                    avg_response_time[service_name] = round(sum(response_time[service_name]) / WINDOW_SIZE, 4)

                return Response(content=response.text, status_code=200)
            except Exception as e:
                return Response(content=f'Failed to connect to service "{service_name}": {str(e)}', status_code=500)

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)


# TODO:
# - test the least respoonse time policy and figure out how to get number of active connections to a container
# - build the resoruce based policy
#   - add constraints on the containers and determine their current usage to choose the next best container
# - testing of above policies for the correctness
# - determine the metric to measure the performance and cost w.r.t. the different workloads
#   - check performance with and without the load balancer
# - auto-scaling the containers
# - generate the different behaviors of workload to test
