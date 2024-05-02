
# This file defines a Flask application that acts as a backend service.

# default imports
from flask import Flask
import random

# create a Flask application
app = Flask(__name__)

# global variable to keep track of the request count
req_count = 0

@app.route("/")
def service():
    global req_count
    req_count += 1

    x = [random.randint(1, 100) for i in range(100000)]
    x.sort()

    # Write the count to a file
    with open("req_count.txt", "w") as file:
        file.write("Access count: ")
        file.write(str(req_count))
        file.write("\n")

    html = '<html><body><h1>Hello World!</h1><p>Access count: ' + \
            str(req_count) + '</p></body></html>' # + \
            # '<img src="https://media.giphy.com/media/3o7TKz9bX9v6hZ8NSA/giphy.gif">' + \
            # '</body></html>'
    return html
