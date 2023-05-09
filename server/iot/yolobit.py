import sys
import json
import time
import threading
import cv2
import pathlib
from  Adafruit_IO import  MQTTClient, Client

from track.helperFunctions import SimulateData

class Yolobit:
    AIO_FEED_IDS = ["yolo.humi", "yolo.temp", "yolo.light", "yolo.bike-locate", "yolo.constraint"]
    AIO_USERNAME = "phuckhang2611"
    AIO_KEY = "aio_Srto85e4YK5lxylRXc8f5pa0c6RD"
    constraint = {
        "temp": 80,
        "humi": 35.0
    }

    def __init__(self):
        # self.connectMQTTClient()
        self.data = {
            "temp" : "loading...",
            "humi" : "loading...",
            "wind" : "Off",
            "pump" : "Off",
        }        
        self.simulate = None

    def connected(self, client):
        print("Connect successful...")
        for feed in Yolobit.AIO_FEED_IDS:
            self.client.subscribe(feed)

    def subscribe(self, client , userdata , mid , granted_qos):
        print("Subcribe successful...")

    def disconnected(self, client):
        print("Break connection...")
        sys.exit(1)

    def updateWind(self):
        if int(self.data["humi"]) >= Yolobit.constraint["humi"]:
            self.data["wind"] = "On"
        else:
            self.data["wind"] = "Off"

    def updatePump(self):
        if float(self.data["temp"]) >= Yolobit.constraint["temp"]:
            self.data["pump"] = "On"
        else:
            self.data["pump"] = "Off"

    def updateContraint(self):
        aio = Client(Yolobit.AIO_USERNAME, Yolobit.AIO_KEY)
        feed_id = 'yolo.constraint'
        data = aio.receive(feed_id)
        payload = data.value
        tempVal, humiVal = payload.split("|")
        Yolobit.constraint["temp"] = int(tempVal)
        Yolobit.constraint["humi"] = float(humiVal)
        print(f"""Updated Yolobit constraint
        Temperature: {Yolobit.constraint["temp"]}
        Huminity: {Yolobit.constraint["humi"]}""")

    def message(self, client , feed_id , payload):
        if feed_id == "yolo.temp":
            self.data["temp"] = payload
            self.updatePump()
            print("Adafruit get temperature data: " + payload + " *C")
        elif feed_id == "yolo.humi":
            self.data["humi"] = payload
            self.updateWind()
            print("Adafruit get huminity data: " + payload + " %")
        elif feed_id == "yolo.bike-locate":
            print("Adafruit bike location data: " + payload)
        elif feed_id == "yolo.light":
            print("Adafruit get light data: " + payload)
        elif feed_id == "yolo.constraint":
            print("Adafruit get constraint data: " + payload)

    def location(self, information):
        x = json.loads(information)
        return x["id"], x["pos"]

    def connectMQTTClient(self):
        self.client = MQTTClient(Yolobit.AIO_USERNAME , Yolobit.AIO_KEY)
        self.client.on_connect = self.connected
        self.client.on_disconnect = self.disconnected
        self.client.on_message = self.message
        self.client.on_subscribe = self.subscribe
        self.client.connect()
        self.client.loop_background()
        self.updateContraint()

    def callDatabase(self, key):
        with open('server\database\\vehicles.json', 'r') as f:
            data = json.load(f)
        result = next((item for item in data if item['key'] == key), None)
        if result is not None:
            print(key, result["pos"])
            return result["pos"]
        else:
            return "Not found!"
        
    def publishVehiclePark(self, vehicle_id, pos):
        if self.simulate is not None: return
        self.client.publish("yolo.bike-locate", vehicle_id+":"+pos[6:])

    def runSimulateMode(self):
        self.simulate = SimulateData()
        threading.Timer(0, self.simulateData).start()

    def simulateData(self):        
        while True:
            # self.client.publish("yolo.temp", self.simulate.random_temp_data())
            # self.client.publish("yolo.humi", self.simulate.random_humi_data())
            self.message(self, "yolo.temp", self.simulate.random_temp_data())
            self.message(self, "yolo.humi", self.simulate.random_humi_data())

            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break
            time.sleep(5)

    def getData(self, field):
        return self.data[field]
    
# iot = Yolobit()