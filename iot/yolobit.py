import serial.tools.list_ports
import random
import time
import  sys
from  Adafruit_IO import  MQTTClient

class Yolobit:
    AIO_FEED_IDS = ["yolo.humi", "yolo.temp"]


    AIO_USERNAME = "phuckhang2611"
    AIO_KEY = "aio_Scpo8249ezAeCDFzsmgKumsn6CrK"
    def __init__(self):
        # AIO_FEED_IDS = ["bbc-led", "bbc-led-1", "bbc-temp", "bbc-humi", "bbc-temp-1", "bbc-humi-1"]
        self.client = MQTTClient(Yolobit.AIO_USERNAME , Yolobit.AIO_KEY)
        self.client.on_connect = self.connected
        self.client.on_disconnect = self.disconnected
        self.client.on_message = self.message
        self.client.on_subscribe = self.subscribe
        self.client.connect()
        self.client.loop_background()

        self.isMicrobitConnected = False
        if self.getPort() != "None":
            self.ser = serial.Serial( port=self.getPort(), baudrate=115200)
            self.isMicrobitConnected = True

        self.mess = "" 
    def  connected(self, client):
        print("Ket noi thanh cong...")
        for feed in Yolobit.AIO_FEED_IDS:
            client.subscribe(feed)

    def  subscribe(self, client , userdata , mid , granted_qos):
        print("Subcribe thanh cong...")

    def  disconnected(self, client):
        print("Ngat ket noi...")
        sys.exit (1)

    def  message(self, client , feed_id , payload):
        print("Nhan du lieu: " + payload)
        if self.isMicrobitConnected:
            self.ser.write((str(payload) + "#").encode())


    def getPort(self):
        ports = serial.tools.list_ports.comports()
        N = len(ports)
        commPort = "None"
        for i in range(0, N):
            port = ports[i]
            strPort = str(port)
            if "USB Serial Device" in strPort:
                splitPort = strPort.split(" ")
                commPort = (splitPort[0])
        return commPort




    def processData(self, data):
        data = data.replace("!", "")
        data = data.replace("#", "")
        splitData = data.split(":")
        print(splitData)
        try:
            if splitData[0] == "1":
                if splitData[1] == "TEMP":
                    self.client.publish("bbc-temp", splitData[2])
                elif splitData[1] == "HUMI":
                    self.client.publish("bbc-humi", splitData[2])
            if splitData[0] == "2":
                if splitData[1] == "TEMP":
                    self.client.publish("bbc-temp-1", splitData[2])
                elif splitData[1] == "HUMI":
                    self.client.publish("bbc-humi-1", splitData[2])
        except:
            pass

    
    def readSerial(self):
        bytesToRead = self.ser.inWaiting()
        if (bytesToRead > 0):
            global mess
            mess = mess + self.ser.read(bytesToRead).decode("UTF-8")
            while ("#" in mess) and ("!" in mess):
                start = mess.find("!")
                end = mess.find("#")
                self.processData(mess[start:end + 1])
                if (end == len(mess)):
                    mess = ""
                else:
                    mess = mess[end+1:]
    def getTemp(self):
        return 30
    def getHumanity(self):
        return 5
    def getWind(self):
        return True
    def getMog(self):
        return False
        

    def run(self):
        while True:
            if self.isMicrobitConnected:
                self.readSerial()
            time.sleep(1)

Yolobit().run()