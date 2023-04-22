from flask import Flask, request, jsonify
import os
from flask_cors import CORS
import socket
from thread_module import *

SERVER  = {
    "PORT" : 5050,
    "IP" : socket.gethostbyname(socket.gethostname())
}
FORMAT = "utf-8"

path_cwd = os.path.dirname(os.path.realpath(__file__))
path_templates = os.path.join(path_cwd, 'templates')
path_static = os.path.join(path_cwd, 'static')

app = Flask(__name__)
CORS(app)


@app.route("/test", methods=['GET', 'POST'])
def handle_test():
    return "test"


@app.route("/post", methods=['GET', 'POST'])
def handle_post_request():
    data = request.get_json()
    response = f"Server received: {data}"
    return jsonify(response), 200

# def listener(conn, addr):
#     while True:
#         packet = conn.recv(1024).decode(FORMAT)
#         print(packet)

if __name__ == '__main__':
    print(SERVER["IP"])
    # app.run(debug=True)
    app.run(port=SERVER["PORT"], host=SERVER["IP"], debug=True)
    # server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server.bind((SERVER["IP"], SERVER["PORT"]))
    # server.listen(20)
    # while True:
    #     conn, addr = server.accept()
    #     thread = ThreadWithReturnValue(target= listener,args=(conn, addr))
    #     thread.start()