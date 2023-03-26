from flask import Flask, request, jsonify
import os
from flask_cors import CORS

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

if __name__ == '__main__':
    app.run(debug=True)