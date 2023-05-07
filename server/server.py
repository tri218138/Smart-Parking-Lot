from flask import Flask, request, jsonify
import os
from flask_cors import CORS
import socket
import cv2
from flask import Flask, request, jsonify, Response, render_template, redirect
from trackingVehicle import AppTracking
import threading
from iot.yolobit import Yolobit
import time
import random, json

SERVER  = {
    "PORT" : 5050,
    "IP" : socket.gethostbyname(socket.gethostname())
}

FORMAT = "utf-8"
path_cwd = os.path.dirname(os.path.realpath(__file__))
path_templates = os.path.join(path_cwd, 'templates')
path_static = os.path.join(path_cwd, 'static')
iot = Yolobit()

app = Flask(__name__, template_folder="./static/template")
CORS(app)

video_stream_path = "http://192.168.61.215:8080/video"
appTracking = AppTracking()
# thApp = threading.Thread(target=appTracking.run)

# start the data collection thread
data_collection_thread = threading.Thread(target=iot.simulateData)
data_collection_thread.daemon = True  # set the thread to be a daemon thread, so it will exit when the main thread exits
data_collection_thread.start()

def read_json_file(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

def gen_frame():
    while True:
        appTracking.work()
        frame = appTracking.getResultFrame()
        # Encode the frame as an image in JPEG format
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
@app.route("/find_vehicle", methods=["POST"])
def find_vehicle():
    print("hereeee1")
    if request.method == 'POST':
        postData = request.form.to_dict()
        print(postData)
        if 'inputVehicleId' in postData:
            print("hereeee2")
            vehicle_id = postData["inputVehicleId"]
            appTracking.findVehicleId(vehicle_id)
    return redirect("/", code=302)

@app.route("/sensor_data", methods=["GET"])
def get_sensor_data():
    temperature = iot.getData('temp')
    humidity = iot.getData('humi')
    wind = iot.getData('wind')
    return jsonify(temperature=temperature, humidity=humidity, wind=wind)

@app.route("/vehicle_parked_data", methods=["GET"])
def get_vehicle_parked_data():
    return read_json_file('server\database\\vehicle_id.json')
@app.route("/ranges_data", methods=["GET"])
def get_ranges_data_data():
    return appTracking.getAllRanges()

@app.route("/", methods=['GET', 'POST'])
def main_route():
    # wind = iot.getWind()
    # mog = iot.getMog()
    # sensorData = render_template('sensor.html', temperature=sensor_data['temp'], humidity=sensor_data['humi'])
    sensorData = render_template('sensor.html')
    videoData = render_template('video.html', source = f"""http://{SERVER["IP"]}:{SERVER["PORT"]}/api/gatecam""")
    inforData = render_template('information.html', inforData = read_json_file('server\database\\vehicle_id.json'))
    rangesData = render_template('information2.html')
    inputForm = render_template('find_vehicle.html')
    content_ = render_template('layout.html', row1_col1=videoData, row1_col2=inforData, row2_col1=sensorData, row2_col2=rangesData, row2_col3= inputForm)
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
    app.run(port=SERVER["PORT"], host=SERVER["IP"], debug=True, use_reloader=False)