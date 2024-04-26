
# default imports
import argparse
import os
import subprocess
import json
import time

REPLICAS = 4
replica_dtls = {}

# main function
if __name__ == "__main__":

    # build the image for gateway and run the container
    # TODO: take the image names and Dockerfile path from user input
    subprocess.run(" ".join(["bash", "conductor.sh", "build", "test-gateway", "latest", "gateway/."]), shell=True)
    subprocess.run(" ".join(["docker", "run", "-d", "-i", "-p", "8000:8000", "--name", "gateway", "test-gateway:latest"]), shell=True)

    # build the image for frontend service and start the containers with replica
    # TODO: take the replica count from the user input
    subprocess.run(" ".join(["docker", "compose", "up", "--build", "-d", "--scale", "frontend=" + str(REPLICAS)]), shell=True)

    # find the name of the base directory
    base_dir = os.getcwd().split("/")[-1]

    # find the IP and port of the frontend service
    # NOTE: assuming the fronted services are running on same phys machine as gateway
    for i in range(1, REPLICAS+1):

        ip_addr = subprocess.run(" ".join(["docker", "inspect", "-f", "'{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'", "gateway"]), shell=True, capture_output=True).stdout.decode("utf-8").replace("'", "").replace("\n", "")
        port = subprocess.run(" ".join(["docker", "inspect", "-f", "'{{(index (index .NetworkSettings.Ports \"8000/tcp\") 0).HostPort}}'", base_dir + "-frontend-" + str(i)]), shell=True, capture_output=True).stdout.decode("utf-8").replace("'", "").replace("\n", "")
        replica_dtls[base_dir + "_frontend_" + str(i)] = {"ip": ip_addr, "port": port}
        # ip_addr = "127.0.0.1"
        print(ip_addr)
        ip_addr = ip_addr[:-1] + "1"
        print(port)
            # register the frontend service with the gateway via POST
        register_resp = subprocess.run(" ".join(["curl", "-X", "POST", "http://localhost:8000/register", "-H", "\"Content-Type: application/json\"", "-d", f"'{{\"name\": \"{base_dir}-frontend-{str(i)}\", \"ip\": \"{ip_addr}\", \"port\": {port}, \"status\": \"active\"}}'"]), shell=True)
        
    #print(replica_dtls)

    # set the policy for the gateway via POST
    # policy_resp = subprocess.run(" ".join(["curl", "-X", "POST", "http://localhost:8000/policy", "-H", "Content-Type: application/json", "-d", "'{\"policy\": \"LEAST_RESPONSE_TIME\"}'"]), shell=True)
    # print(policy_resp)

    # parse command-line arguments
    # parser = argparse.ArgumentParser()
    # parser.add_argument("--input", type=str, help="Path to the input file")
    # parser.add_argument("--output", type=str, help="Path to the output file")
    # args = parser.parse_args()

    # # load data from the input file
    # with open(args.input, "r") as f:
    #     data = json.load(f)

    # # Process the data
    # processed_data = data

    # # Save the processed data to the output file
    # with open(args.output, "w") as f:
    #     json.dump(processed_data, f)

