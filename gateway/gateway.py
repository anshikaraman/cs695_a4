
# This script defines a Flask application that acts as a gateway to route incoming requests to two different services.

# default imports
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
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

# local variables to store the details of the frontend services
FRONTEND_DTLS = {}
req_count = {}; round_robin_idx = 0
response_time = {}
min_service_name = None

# define the policy for load balancing
POLICY = "LEAST_RESPONSE_TIME"

# define route to accept details about frontend services
@app.post("/register")
def register_frontend(container: ContainerDetails):
    global FRONTEND_DTLS, response_time

    # add the details of the frontend service to the dictionary
    if container.status == "active":
        FRONTEND_DTLS[container.name] = f"http://{container.name}:7000"
        req_count[container.name] = 0
        response_time[container.name] = 0
        # print(FRONTEND_DTLS)
        return {'message': f'Registered frontend service "{container.name}"'}

    elif container.status == "inactive":
        if container.name in FRONTEND_DTLS:
            del FRONTEND_DTLS[container.name]
            return {'message': f'Removed frontend service "{container.name}"'}

# define a route to accept the load balancing policy
# @app.post("/policy")
# def register_balancing_policy(policy: Query[str]):
#     return {'message': 'Policy set to ' + policy}

# define a route to accept incoming requests
@app.get("/")
def load_balancer():
    global FRONTEND_DTLS, req_count, round_robin_idx, response_time, min_service_name, POLICY

    # for round-robin policy
    if POLICY == "ROUND_ROBIN":
        service_name = list(FRONTEND_DTLS.keys())[round_robin_idx % len(FRONTEND_DTLS)]
        service_endpoint = FRONTEND_DTLS[service_name]

        # increment the round-robin index after selecting the service
        round_robin_idx += 1

        try:
            response = requests.get(service_endpoint)
            # increment the request count
            req_count[service_name] += 1
            return HTMLResponse(content=f'Hello from the service "{service_name}"! Request count: {req_count[service_name]}', status_code=200)
        except Exception as e:
            return HTMLResponse(content=f'Failed to connect to service "{service_name}": {str(e)}', status_code=500)

    # for least response time policy
    elif POLICY == "LEAST_RESPONSE_TIME":
        min_time = min(response_time.values())

        for service_name, service_endpoint in FRONTEND_DTLS.items():

            try:
                if response_time[service_name] == min_time:
                    min_service_name = service_name
                    # print(); print("Service name: ", end="")
                    # print(FRONTEND_DTLS[min_service_name])

                    response = requests.get(FRONTEND_DTLS[min_service_name])

                    # compute the average response time
                    elapsed_time = response.elapsed.total_seconds()
                    response_time[service_name] = round(((response_time[service_name] * req_count[service_name]) + elapsed_time) / (req_count[service_name] + 1), 4)
                    # increment the request count
                    req_count[service_name] += 1

                    # print("Response time: ", end="")
                    # print(response_time); print()
                    return HTMLResponse(content=response.text, status_code=200)
                else:
                    continue

            except Exception as e:
                return HTMLResponse(content=f'Failed to connect to service "{service_name}": {str(e)}', status_code=500)

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
