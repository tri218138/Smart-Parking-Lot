import cv2
from datetime import datetime, timedelta
import numpy as np
import threading
from track.helperFunctions import is_rect_inside_another, read_json_file, write_json_file
from track.euclideanDistTracker import EuclideanDistTracker
import pathlib

HOME_PATH = pathlib.Path(__file__).parent.parent

class Frame:
    def __init__(self):
        self.main = None
        self.special = None
        self.first = None
        self.roi = None
        self.mask = None
        self.empty = None
        self.contour = None

class AppTracker:
    vehicleArea = 30.0
    emptyArea = 100.0

    def __init__(self, path="server/public/videos/video1.mp4"):
        self.path = path
        self.cap = cv2.VideoCapture(path)
        self.object_detector = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=50, detectShadows=False)
        self.trackerED = EuclideanDistTracker()
        self.frames = Frame()

        self.ret, self.frames.main = self.cap.read()

        # self.mTT = MeasureTakenTime()

        self.frames.special = {
            "gate": [600, 70, self.frames.main.shape[1] - 600 - 80, 70]
        }
        self.frames.roi = self.getRoi(self.frames.main, self.getSpecialFrame())

        self.isSettingRanges = False
        self.ranges = []

        self.frames.first = None

        self.collectFirstFrame()
        self.loadMultiRanges()

    def showFrames(self):
        future = datetime.now() + timedelta(seconds = 2)
        while datetime.now() < future:
            self.work()
        self.trackEmptyInRanges(self.frames.first)
        self.drawPolygonSettings()
        while True:
            cv2.imshow("main", self.frames.main)
            cv2.imshow("mask", self.frames.mask)
            cv2.imshow("roi", self.frames.roi)
            cv2.imshow("ranges", self.frames.first)
            cv2.imshow("empty", self.frames.empty)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break
        cv2.imwrite("server/public/frames/main.jpg", self.frames.main)
        cv2.imwrite("server/public/frames/mask.jpg", self.frames.mask)
        cv2.imwrite("server/public/frames/roi.jpg", self.frames.roi)
        cv2.imwrite("server/public/frames/ranges.jpg", self.frames.first)
        cv2.imwrite("server/public/frames/empty.jpg", self.frames.empty)


    def startMultiThreading(self):
        self.call_function_with_interval_2()

    def call_function_with_interval_2(self):
        if cv2.waitKey(1) == 27:
            return
        self.trackEmptyInRanges(self.frames.main)
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
        # print(list_area)
        return list_area
    
    def notifyVehicleCoordination(self, centerPoint, startTime):
        if datetime.now() - startTime >= timedelta(seconds = 5):
            threading.Timer(0, threading._shutdown).start()
            return        
        threading.Timer(0.1, self.notifyVehicleCoordination, args=(centerPoint, startTime)).start()
        cv2.circle(self.frames.main, centerPoint, 1, (0, 0, 255), 2)
        cv2.circle(self.frames.main, centerPoint, 10, (0, 0, 255), 2)
        cv2.circle(self.frames.main, centerPoint, 15, (0, 0, 255), 2)
        # cv2.imshow("finding", self.frames.main)
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
            if self.frames.empty is None: self.frames.empty = contour_image
            else: self.frames.empty = cv2.bitwise_or(self.frames.empty, contour_image)
            # self.frames.empty = contour_image

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
        return self.frames.main

    def collectFirstFrame(self):
        while not self.ret:
            self.ret, self.frames.main = self.cap.read()
        self.frames.first = self.frames.main

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
                    cv2.circle(self.frames.first,
                               self.ranges[i]["polygon"][0], 1, (0, 255, 0), 5)
                else:
                    cv2.polylines(self.frames.first, [np.array(
                        self.ranges[i]["polygon"])], True, (0, 255, 0), 5)
            if len(self.ranges[-1]["polygon"]) == 1:
                cv2.circle(self.frames.first,
                           self.ranges[-1]["polygon"][0], 1, (0, 0, 255), 5)
            else:
                cv2.polylines(self.frames.first, [np.array(
                    self.ranges[-1]["polygon"])], False if self.isSettingRanges else True, (0, 0, 255) if self.isSettingRanges else (0, 255, 0), 5)

    def setMultiRanges(self):
        if self.frames.first is not None:
            cv2.namedWindow('Set multi ranges')
            cv2.setMouseCallback('Set multi ranges', self.mouse_callback)

            while True:
                self.drawPolygonSettings()
                cv2.imshow('Set multi ranges', self.frames.first)

                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    break
            
            write_json_file('server\database\\ranges.json', self.ranges)

    def loadMultiRanges(self):
        self.ranges = read_json_file('server\database\\ranges.json')

    # def run(self):
    #     # self.setSpecialFrame(cv2.selectROI(self.frames.main), "gate")
    #     # self.setSpecialFrame(cv2.selectROI(self.frames.main), "range A")
    #     # self.setSpecialFrame(cv2.selectROI(self.frames.main), "range B")

    #     # self.setMultiRanges()
    #     self.loadMultiRanges()

    #     while True:
    #         self.ret, self.frames.main = self.cap.read()
    #         if not self.ret:
    #             continue
    #         roi = self.frames.main
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

    #         roi = self.getRoi(self.frames.main, self.getSpecialFrame())

    #         # cv2.imshow("Mask", self.mask)
    #         cv2.imshow("Ranges", self.frames.first)
    #         cv2.imshow("Frame", self.frames.main)
    #         # cv2.imshow("Roi", roi)

    #         key = cv2.waitKey(10)
    #         if key == 27:
    #             break

    #     self.cap.release()
    #     cv2.destroyAllWindows()
    
    def run(self):
        while True:
            self.work()
            cv2.imshow("mask", self.frames.mask)
            cv2.imshow("main", self.frames.main)
            # contours, _ = cv2.findContours(
            #     self.frames.mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            # contour_image = cv2.cvtColor(self.frames.mask, cv2.COLOR_GRAY2BGR)
            # cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 1)
            # cv2.imshow("contour", contour_image)
            key = cv2.waitKey(10)
            if key == 27:
                break

    def work(self):
        self.ret, self.frames.main = self.cap.read()
        if "http" in self.path: return
        roi = self.frames.main
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
        

    def detect(self, roi) -> list():
        mask = self.object_detector.apply(roi)
        detections = []
        
        _, mask = cv2.threshold(
            mask, 254, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # mask = cv2.erode(mask, np.ones((2, 2), np.uint8), iterations=1)
        # mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1)
        self.frames.mask = mask
        
        contours, _ = cv2.findContours(
            mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # old version
        # self.frames.mask = mask
        # contours, _ = cv2.findContours(
        #     mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            if area > AppTracker.vehicleArea:
                detections.append([x, y, w, h])
        return detections

    def setSpecialFrame(self, rect, name="gate"):
        self.frames.special[name] = rect

    def getSpecialFrame(self, name="gate"):
        return self.frames.special[name]

    def getAllSpecialFrames(self):
        return self.frames.special

    def getRoi(self, frame, rect):
        x, y, w, h = rect
        return frame[y:y+h, x:x+w]

# AppTracker().run()
