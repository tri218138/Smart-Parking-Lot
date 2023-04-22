import cv2
from tracker import *
import math
import time
import numpy as np
from helper import *
from vehicle import *

mTT = MeasureTakenTime()

data_path = "server/public/videos/longest.mp4"
cap = cv2.VideoCapture(data_path)

object_detector = cv2.createBackgroundSubtractorMOG2(
    history=200, varThreshold=50, detectShadows=False)

ret, frame = cap.read()

from detectVehicle import *
detector = Detector(frame)

while True:
    ret, frame = cap.read()

    cv2.imshow("Origin", frame)
    detector.update(frame)
    detector.run()
    vehicles = detector.getVehicles()

    key = cv2.waitKey(10)
    if key == 27: break

cap.release()
cv2.destroyAllWindows()