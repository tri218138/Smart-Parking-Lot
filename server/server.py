from flask import Flask, request, jsonify
import os
from flask_cors import CORS
import socket
import cv2
from flask import Flask, request, jsonify, Response, render_template
# from yolobit import *

SERVER  = {
    "PORT" : 5050,
    "IP" : socket.gethostbyname(socket.gethostname())
}
FORMAT = "utf-8"
path_cwd = os.path.dirname(os.path.realpath(__file__))
path_templates = os.path.join(path_cwd, 'templates')
path_static = os.path.join(path_cwd, 'static')
# iot = Yolobit()

app = Flask(__name__, template_folder="./static/template")
CORS(app)

def gen_frame():
    camera = cv2.VideoCapture("http://192.168.1.206:8080/video")
    while True:
        ret, frame = camera.read()  # Read a frame from the camera
        if not ret:
            break
        # Encode the frame as an image in JPEG format
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    camera.release()

@app.route("/", methods=['GET', 'POST'])
def main_route():
    # temperature = iot.getTemp()
    # humanity = iot.getHumanity()
    # wind = iot.getWind()
    # mog = iot.getMog()
    temperature, humanity = 30, 5
    sensorData = render_template('sensor.html', temperature=temperature, humanity=humanity)
    videoData = render_template('video.html')
    content_ = render_template('layout.html', left=sensorData, right=videoData)
    return render_template('index.html', content=content_)

@app.route("/test", methods=['GET', 'POST'])
def handle_test():
    return "test"


@app.route("/post", methods=['GET', 'POST'])
def handle_post_request():
    data = request.get_json()
    response = f"Server received: {data}"
    return jsonify(response), 200


@app.route("/api/gatecam", methods=['GET'])
def handle_gatecam():
    return Response(gen_frame(), mimetype='multipart/x-mixed-replace; boundary=frame', status = 200)

if __name__ == '__main__':
    print(SERVER["IP"])
    app.run(port=SERVER["PORT"], host=SERVER["IP"], debug=True)