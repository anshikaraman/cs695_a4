
# default imports
import argparse
import subprocess
import time

replica_dtls = {}

# main function
if __name__ == "__main__":

    # parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--phys-machine", type=str, nargs='+', help="IP address of the physical machine", required=True)
    parser.add_argument("--usernames", type=str, nargs='+', help="Usernames of the physical machine", required=True)
    parser.add_argument("--port", type=int, nargs='+', help="Port number to run the gateway service", required=True)
    parser.add_argument("--replicas", type=int, nargs='+', help="Number of replicas to start", required=True)
    parser.add_argument("--policy", type=str, help="Load balancing policy to use", default="ROUND_ROBIN")
    parser.add_argument
    args = parser.parse_args()

    # store the command-line arguments
    phys_machine = args.phys_machine
    usernames = args.usernames
    port = args.port
    replicas = args.replicas
    policy = args.policy

    # check if the number of physical machines is equal to the number of usernames
    if len(phys_machine) != len(usernames):
        raise ValueError("Number of physical machines and usernames should be equal")
        exit(1)

    # check if the number of ports is equal to the number of physical machines
    if len(phys_machine) != len(port):
        raise ValueError("Number of physical machines and ports should be equal")
        exit(1)

    # set the docker context to the local machine
    subprocess.run(" ".join(["docker", "context", "use", "default"]), shell=True)

    # build the image for gateway and run the container
    subprocess.run(" ".join(["docker", "build", "-t", "test-gateway:latest", "gateway/."]), shell=True)
    subprocess.run(" ".join(["docker", "run", "-d", "-i", "-p", "8000:8000", "--name", "gateway", "test-gateway:latest"]), shell=True)

    # wait for the gateway to start
    time.sleep(1)

    # set the docker context to the remote machine
    for i in range(len(phys_machine)):
        # set the context to the remote machine
        subprocess.run(" ".join(["docker", "context", "create", usernames[i], "--docker", "host=ssh://"+usernames[i]+"@"+phys_machine[i]]), shell=True)
        subprocess.run(" ".join(["docker", "context", "use", usernames[i]]), shell=True)

        # build the image for backend service and start the containers with replica
        subprocess.run(" ".join(["docker", "build", "-t", "test-backend:latest", "backend/."]), shell=True)
        for j in range(1, replicas[i]+1):
            subprocess.run(" ".join(["docker", "run", "-d", "-i", "-p", str(port[i]+j)+":7000", "--name", "backend"+str(j), "test-backend:latest"]), shell=True)

        # find the IP and port of the backend service
        # NOTE: assuming the fronted services are running on same phys machine as gateway
        for k in range(1, replicas[i]+1):
            container_name = "backend" + str(k)

            ip_addr = phys_machine[i]
            port = subprocess.run(" ".join(["docker", "inspect", "-f", "'{{(index (index .NetworkSettings.Ports \"7000/tcp\") 0).HostPort}}'", container_name]), shell=True, capture_output=True).stdout.decode("utf-8").replace("'", "").replace("\n", "")

            replica_dtls[usernames[i]+"-"+container_name] = {"ip": ip_addr, "port": port}

            # register the backend service with the gateway via POST
            register_resp = subprocess.run(" ".join(["curl", "-X", "POST", "http://localhost:8000/register", "-H", "Content-Type: application/json", "-d", f"'{{\"name\": \"{usernames[i]}-{container_name}\", \"ip\": \"{ip_addr}\", \"port\": {port}, \"status\": \"active\"}}'"]), shell=True)

    # print the details of the replicas
    print("Replica details:")
    for k, v in replica_dtls.items():
        print(f"{k}: {v}")

    # set the policy for the gateway via POST
    policy_resp = subprocess.run(" ".join(["curl", "-X", "POST", "http://localhost:8000/set-policy?policy="+policy]), shell=True)

    print()
    print("Gateway service started successfully")

    while True:

        # ask the user the below options to choose from
        option = input("Select an option:\n1. Stop all services and Exit\n2. Kill a replica\n3. Start a replica\nEnter the option:")

        # stop all services
        if option == "1":
            # set the docker context to the local machine
            subprocess.run(" ".join(["docker", "context", "use", "default"]), shell=True)

            # stop the gateway service
            subprocess.run(" ".join(["docker", "stop", "gateway"]), shell=True)
            subprocess.run(" ".join(["docker", "rm", "gateway"]), shell=True)

            # stop the backend services
            for i in range(len(phys_machine)):

                # set the context to the remote machine
                subprocess.run(" ".join(["docker", "context", "use", usernames[i]]), shell=True)

                for j in range(1, replicas[i]+1):
                    container_name = "backend" + str(j)
                    subprocess.run(" ".join(["docker", "stop", container_name]), shell=True)
                    subprocess.run(" ".join(["docker", "rm", container_name]), shell=True)

            # remove the docker context
            for i in range(len(phys_machine)):
                subprocess.run(" ".join(["docker", "context", "use", "default"]), shell=True)
                subprocess.run(" ".join(["docker", "context", "rm", usernames[i]]), shell=True)

            print("Stopped the services successfully")
            exit(0)

        # kill a replica
        elif option == "2":
            # ask the user for the replica to kill
            replica_name = input("Enter the replica name to kill: ")

            # set the context to the remote machine
            subprocess.run(" ".join(["docker", "context", "use", replica_name.split("-")[0]]), shell=True)

            # kill the replica
            subprocess.run(" ".join(["docker", "stop", replica_name.split("-")[1]]), shell=True)
            subprocess.run(" ".join(["docker", "rm", replica_name.split("-")[1]]), shell=True)

            # remove the replica details from the dictionary
            del replica_dtls[replica_name]

            # register the backend service with the gateway via POST
            register_resp = subprocess.run(" ".join(["curl", "-X", "POST", "http://localhost:8000/register", "-H", "Content-Type: application/json", "-d", f"'{{\"name\": \"{usernames[i]}-{container_name}\", \"ip\": \"0.0.0.0\", \"port\": 0, \"status\": \"inactive\"}}'"]), shell=True)

            print(f"Killed the replica {replica_name} successfully")

        # start a replica
        elif option == "3":
            # ask the user for the replica to start
            replica_name = input("Enter the replica name to start: ")

            # set the context to the remote machine
            subprocess.run(" ".join(["docker", "context", "use", replica_name.split("-")[0]]), shell=True)

            # filter the replica details from the dictionary based on the remote machine
            replica_dtls_filtered = {k: v for k, v in replica_dtls.items() if k.split("-")[0] == replica_name.split("-")[0]}
            # determine the port number for the new replica
            port = max([int(v["port"]) for v in replica_dtls_filtered.values()]) + 1

            # start the replica
            subprocess.run(" ".join(["docker", "run", "-d", "-i", "-p", str(port)+":7000", "--name", replica_name, "test-backend:latest"]), shell=True)

            # add the replica details to the dictionary
            replica_dtls[replica_name] = {"ip": replica_dtls_filtered[0]["ip"], "port": port}

            # register the backend service with the gateway via POST
            register_resp = subprocess.run(" ".join(["curl", "-X", "POST", "http://localhost:8000/register", "-H", "Content-Type: application/json", "-d", f"'{{\"name\": \"{replica_name}\", \"ip\": \"{replica_dtls_filtered[0]['ip']}\", \"port\": {port}, \"status\": \"active\"}}'"]), shell=True)

            print(f"Started the replica {replica_name} successfully")

