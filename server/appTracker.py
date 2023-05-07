import cv2
from tracker import *
import math
import time
from datetime import datetime, timedelta
import numpy as np
from scipy import stats, polyfit
import json
import threading
from helperFunctions import is_rect_inside_another, read_json_file, write_json_file
from vehicle import Vehicle
from euclideanDistTracker import EuclideanDistTracker

class AppTracker:
    vehicleArea = 30.0
    emptyArea = 100.0

    def __init__(self, path="server/public/videos/longest.mp4"):
        self.cap = cv2.VideoCapture(path)
        self.object_detector = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=50, detectShadows=False)
        self.trackerED = EuclideanDistTracker()

        self.ret, self.frame = self.cap.read()

        # self.mTT = MeasureTakenTime()

        self.specialFrame = {
            "gate": [600, 70, self.frame.shape[1] - 600 - 80, 70]
        }

        self.isSettingRanges = False
        self.ranges = []

        self.firstFrame = None

        self.collectFirstFrame()
        self.loadMultiRanges()

        self.call_function_with_interval_2()

    def call_function_with_interval_2(self):
        self.trackEmptyInRanges(self.frame)
        threading.Timer(2.0, self.call_function_with_interval_2).start()

    def getPolygonFrame(self, frame, polygon):
        mask = np.zeros_like(frame[:, :, 0])
        cv2.fillPoly(mask, [np.array(polygon)], 255)
        sub_frame = cv2.bitwise_and(frame, frame, mask=mask)
        return sub_frame

    def getAreaOfEmptyInRanges(self, contours):
        list_area = []
        for contour in contours:
            area = cv2.contourArea(contour)
            list_area.append(area)
            list_area.sort(reverse=True)
        return list_area
    
    def notifyVehicleCoordination(self, centerPoint, startTime):
        if datetime.now() - startTime >= timedelta(seconds = 5):
            threading.Timer(0, threading._shutdown).start()
            return        
        threading.Timer(0.1, self.notifyVehicleCoordination, args=(centerPoint, startTime)).start()
        cv2.circle(self.frame, centerPoint, 1, (0, 0, 255), 2)
        cv2.circle(self.frame, centerPoint, 10, (0, 0, 255), 2)
        cv2.circle(self.frame, centerPoint, 15, (0, 0, 255), 2)
        # cv2.imshow("finding", self.frame)
        # cv2.waitKey(0)

    def convertTupleStringToInt(self, string_):
        return tuple(map(int, string_.strip("()").split(",")))
    
    def findVehicleId(self, key):
        existing_data = read_json_file('server\database\\vehicles.json')
        for vehicle in existing_data:
            if vehicle["key"] == key:
                point = np.array(self.convertTupleStringToInt(vehicle["coor"]))
                self.notifyVehicleCoordination(point, startTime=datetime.now())
                return vehicle["pos"]

    def trackEmptyInRanges(self, frame):
        for idx, range_ in enumerate(self.ranges):
            polygon_frame = self.getPolygonFrame(
                frame, range_["polygon"])

            gray_frame = cv2.cvtColor(polygon_frame, cv2.COLOR_BGR2GRAY)
            _, binary_image = cv2.threshold(
                gray_frame, 127, 255, cv2.THRESH_BINARY)

            # Find contours
            contours, _ = cv2.findContours(
                binary_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            
            contour_image = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
            cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 2)

            empty_areas = self.getAreaOfEmptyInRanges(contours)
            
            # """Debug mode"""
            # cv2.imshow(f"Empty range {idx}", contour_image)
            # cv2.waitKey(0)

            if empty_areas[0] >= AppTracker.emptyArea:
                self.ranges[idx]["empty"] = True
            else:
                self.ranges[idx]["empty"] = False

    def getAllRanges(self):
        return self.ranges

    def getResultFrame(self):
        return self.frame

    def collectFirstFrame(self):
        while not self.ret:
            self.ret, self.frame = self.cap.read()
        self.firstFrame = self.frame

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if not self.isSettingRanges:
                self.ranges.append({
                    "polygon": [],
                    "id": f"range {chr(len(self.ranges) + 65)}",
                })
                self.isSettingRanges = True
            self.ranges[-1]["polygon"].append([x, y])
        if event == cv2.EVENT_RBUTTONDOWN:
            self.ranges[-1]["polygon"].append(self.ranges[-1]["polygon"][0])
            self.isSettingRanges = False

    def drawPolygonSettings(self):
        if len(self.ranges) > 0:
            for i in range(0, len(self.ranges) - 1):
                if len(self.ranges[i]["polygon"]) == 1:
                    cv2.circle(self.firstFrame,
                               self.ranges[i]["polygon"][0], 1, (0, 255, 0), 5)
                else:
                    cv2.polylines(self.firstFrame, [np.array(
                        self.ranges[i]["polygon"])], True, (0, 255, 0), 5)
            if len(self.ranges[-1]["polygon"]) == 1:
                cv2.circle(self.firstFrame,
                           self.ranges[-1]["polygon"][0], 1, (0, 0, 255), 5)
            else:
                cv2.polylines(self.firstFrame, [np.array(
                    self.ranges[-1]["polygon"])], False if self.isSettingRanges else True, (0, 0, 255) if self.isSettingRanges else (0, 255, 0), 5)

    def setMultiRanges(self):
        if self.firstFrame is not None:
            cv2.namedWindow('Set multi ranges')
            cv2.setMouseCallback('Set multi ranges', self.mouse_callback)

            while True:
                self.drawPolygonSettings()
                cv2.imshow('Set multi ranges', self.firstFrame)

                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    break
            
            write_json_file('server\database\\ranges.json', self.ranges)

    def loadMultiRanges(self):
        self.ranges = read_json_file('server\database\\ranges.json')

    # def run(self):
    #     # self.setSpecialFrame(cv2.selectROI(self.frame), "gate")
    #     # self.setSpecialFrame(cv2.selectROI(self.frame), "range A")
    #     # self.setSpecialFrame(cv2.selectROI(self.frame), "range B")

    #     # self.setMultiRanges()
    #     self.loadMultiRanges()

    #     while True:
    #         self.ret, self.frame = self.cap.read()
    #         if not self.ret:
    #             continue
    #         roi = self.frame
    #         detected_rect = self.detect(roi)

    #         specFrame = self.getSpecialFrame()
    #         detected_rect_roi = [
    #             rect for rect in detected_rect if is_rect_inside_another(rect, specFrame)]

    #         self.trackerED.addNewTracker(detected_rect_roi)
    #         boxes_ids = self.trackerED.updateOldTracker(detected_rect)
    #         self.trackerED.checkParkedVehicle(self.ranges)
    #         self.trackerED.removeDuplicate()

    #         self.drawPolygonSettings()

    #         for box_id in boxes_ids:
    #             x, y, w, h, id = box_id
    #             cv2.putText(roi, str(id), (x, y - 10),
    #                         cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)
    #             cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 1)

    #         roi = self.getRoi(self.frame, self.getSpecialFrame())

    #         # cv2.imshow("Mask", self.mask)
    #         cv2.imshow("Ranges", self.firstFrame)
    #         cv2.imshow("Frame", self.frame)
    #         # cv2.imshow("Roi", roi)

    #         key = cv2.waitKey(10)
    #         if key == 27:
    #             break

    #     self.cap.release()
    #     cv2.destroyAllWindows()

    def work(self):
        self.ret, self.frame = self.cap.read()
        roi = self.frame
        detected_rect = self.detect(roi)

        specFrame = self.getSpecialFrame()
        detected_rect_roi = [
            rect for rect in detected_rect if is_rect_inside_another(rect, specFrame)]

        self.trackerED.addNewTracker(detected_rect_roi)
        boxes_ids = self.trackerED.updateOldTracker(detected_rect)
        # self.trackerED.checkParkedVehicle(self.getAllSpecialFrames())
        self.trackerED.checkParkedVehicle(self.ranges)
        self.trackerED.removeDuplicate()

        # self.trackEmptyInRanges(copy.copy(roi))

        for box_id in boxes_ids:
            x, y, w, h, id = box_id
            cv2.putText(roi, str(id), (x, y - 10),
                        cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)
            cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 1)

        roi = self.getRoi(self.frame, self.getSpecialFrame())

    def detect(self, roi) -> list():
        mask = self.object_detector.apply(roi)
        detections = []

        _, self.mask = cv2.threshold(
            mask, 254, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(
            mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            if area > AppTracker.vehicleArea:
                detections.append([x, y, w, h])
        return detections

    def setSpecialFrame(self, rect, name="gate"):
        self.specialFrame[name] = rect

    def getSpecialFrame(self, name="gate"):
        return self.specialFrame[name]

    def getAllSpecialFrames(self):
        return self.specialFrame

    def getRoi(self, frame, rect):
        x, y, w, h = rect
        return frame[y:y+h, x:x+w]

# AppTracker().run()
