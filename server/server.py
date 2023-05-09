from flask import Flask, request, jsonify, Response, render_template, redirect
from flask_cors import CORS
import os
import socket
import sys
import cv2
from iot.yolobit import Yolobit
from track.appTracker import AppTracker
from track.helperFunctions import read_json_file, write_json_file

SERVER  = {
    "PORT" : 5050,
    "IP" : socket.gethostbyname(socket.gethostname())
}
FORMAT = "utf-8"

path_cwd = os.path.dirname(os.path.realpath(__file__))
path_templates = os.path.join(path_cwd, 'templates')
path_static = os.path.join(path_cwd, 'static')


app = Flask(__name__, template_folder="./static/template")
CORS(app)

iot = Yolobit()

video_stream_path = "http://192.168.61.215:8080/video"
# appTracker = AppTracker(video_stream_path)
appTracker = AppTracker()

def gen_frame():
    while True:
        appTracker.work()
        frame = appTracker.getResultFrame()
        # Encode the frame as an image in JPEG format
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
@app.route("/user/input/vehicle_id", methods=["POST"])
def find_vehicle():
    if request.method == 'POST':
        postData = request.form.to_dict()
        if 'inputVehicleId' in postData:
            vehicle_id = postData["inputVehicleId"]
            pos = appTracker.findVehicleId(vehicle_id)
            iot.publishVehiclePark(vehicle_id, pos)
    return redirect("/", code=302)

@app.route("/data/sensor", methods=["GET"])
def get_sensor_data():
    temperature = iot.getData('temp')
    humidity = iot.getData('humi')
    wind = iot.getData('wind')
    pump = iot.getData('pump')
    return jsonify(temperature=temperature, humidity=humidity, wind=wind, pump=pump)

@app.route("/data/vehicle_park", methods=["GET"])
def get_vehicle_park_data():
    return read_json_file('server\database\\vehicles.json')

@app.route("/data/ranges", methods=["GET"])
def get_ranges_data_data():
    return appTracker.getAllRanges()

@app.route("/", methods=['GET', 'POST'])
def main_route():
    sensorData = render_template('sensor.html')
    videoData = render_template('video.html', source = f"""http://{SERVER["IP"]}:{SERVER["PORT"]}/api/gatecam""")
    vehicleParkData = render_template('vehicle_park.html', inforData = read_json_file('server\database\\vehicles.json'))
    rangesData = render_template('range_state.html')
    inputForm = render_template('find_vehicle.html')
    content_ = render_template('layout.html', row1_col1=videoData, row1_col2=vehicleParkData, row2_col1=sensorData, row2_col2=rangesData, row2_col3= inputForm)
    return render_template('index.html', content=content_)

@app.route("/api/gatecam", methods=['GET'])
def handle_gatecam():
    return Response(gen_frame(), mimetype='multipart/x-mixed-replace; boundary=frame', status = 200)

if __name__ == '__main__':
    print("Ip server", SERVER["IP"])
    if "clear" in sys.argv:
        if "ranges" in sys.argv:
            n = input("Confirm 1|0: ")
            if n == "1":
                write_json_file('server\database\\ranges.json', [])
        if "vehicles" in sys.argv:
            write_json_file('server\database\\vehicles.json', [])
    elif "init_range" in sys.argv:
        appTracker.setMultiRanges()
    elif "show_frame" in sys.argv:
        appTracker.showFrames()
    elif "test" in sys.argv:
        appTracker.run()
    else:
        if "simulate" in sys.argv:
            iot.runSimulateMode()
        else:
            iot.connectMQTTClient()
        write_json_file('server\database\\vehicles.json', [])
        appTracker.startMultiThreading()
        app.run(port=SERVER["PORT"], host=SERVER["IP"], debug=True, use_reloader=False)