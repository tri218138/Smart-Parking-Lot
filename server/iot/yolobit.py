import json
import time
import sys
import threading
from  Adafruit_IO import  MQTTClient
from helperFunctions import SimulateData

class Yolobit:
    AIO_FEED_IDS = ["yolo.humi", "yolo.temp", "yolo.bike-db", "yolo.bike-locate"]
    AIO_USERNAME = "phuckhang2611"
    AIO_KEY = "aio_yFQq06eTa1GFVaWUwJdOkdO6zKBe"

    def __init__(self):
        self.simulate = SimulateData()
        # self.connectMQTTClient()
        self.data = {
            "temp" : "loading...",
            "humi" : "loading...",
            "wind" : "Off",
        }

        threading.Timer(0, self.simulateData).start()

    def connected(self, client):
        print("Connect successful...")
        for feed in Yolobit.AIO_FEED_IDS:
            self.client.subscribe(feed)

    def subscribe(self, client , userdata , mid , granted_qos):
        print("Subcribe successful...")

    def disconnected(self, client):
        print("Break connection...")
        sys.exit(1)

    def message(self, client , feed_id , payload):
        if feed_id == "yolo.temp":
            self.data["temp"] = payload
            print("Adafruit get temperature data: " + payload + " *C")
        elif feed_id == "yolo.humi":
            self.data["humi"] = payload
            print(payload, type(payload))
            if int(payload) >= 50:
                self.data["wind"] = "On"
            else:
                self.data["wind"] = "Off"
            print("Adafruit get huminity data: " + payload + " %")
        elif feed_id == "yolo.bike-locate":
            print("Adafruit nhan du lieu vi tri day xe: " + payload)
        elif feed_id == "yolo.bike-db":
            print("Adafruit nhan du lieu bien so xe: " + payload)

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

    def callDatabase(self, key):
        with open('server\database\\vehicles.json', 'r') as f:
            data = json.load(f)
        result = next((item for item in data if item['key'] == key), None)
        if result is not None:
            print(key, result["pos"])
            return result["pos"]
        else:
            return "Not found!"

    def simulateData(self):
        # print("simulate data")
        while True:
            # self.client.publish("yolo.temp", "{:.2f}".format(self.simulate.random_temp_data()))
            # self.client.publish("yolo.humi", "{:.2f}".format(self.simulate.random_humi_data()))
            self.data["temp"] = self.simulate.random_temp_data()
            self.data["humi"] = self.simulate.random_humi_data()
            if int(self.data["humi"]) >= 50:
                self.data["wind"] = "On"
            else:
                self.data["wind"] = "Off"
            # print(self.data)
            time.sleep(2)

    def getData(self, field):
        return self.data[field]
    
# iot = Yolobit()