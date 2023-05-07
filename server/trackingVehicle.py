import cv2
from tracker import *
import math
import time
from datetime import datetime, timedelta
import numpy as np
from scipy import stats, polyfit
# from polyROISelector import polyROISelector
from sklearn.linear_model import LinearRegression
import json
import random
import threading
import string
import copy


def is_rect_inside_another(rect1, rect2):
    if rect1[0] >= rect2[0] and rect1[1] >= rect2[1] and rect1[0] + rect1[2] <= rect2[0] + rect2[2] and rect1[1] + rect1[3] <= rect2[1] + rect2[3]:
        return True
    else:
        return False


def is_point_inside_rect(p, rect):
    x, y = p
    if x >= rect[0] and x <= rect[0] + rect[2] and y >= rect[1] and y <= rect[1] + rect[3]:
        return True
    else:
        return False


def point_inside_polygon(point, polygon):
    # Convert the point and polygon to numpy arrays
    point = (int(point[0]), int(point[1]))
    polygon = np.array(polygon, dtype=np.int32)

    # Use the PointPolygonTest function to check if the point is inside the polygon
    result = cv2.pointPolygonTest(polygon, point, False)

    # Return True if the point is inside the polygon, False otherwise
    return result >= 0


def generate_random_vehicle_id():
    digits = random.choices(string.digits, k=2)
    uppercase_alpha = random.choice(string.ascii_uppercase)
    separator = '-'
    more_digits = random.choices(string.digits, k=5)

    random_string = ''.join(
        digits + [uppercase_alpha] + [separator] + more_digits)
    return random_string


def updateVehicleIdJsonData(new_data):
    with open('server\database\\vehicle_id.json', 'r') as file:
        existing_data = json.load(file)

    existing_data += new_data

    # Write the updated object back to the JSON file
    with open('server\database\\vehicle_id.json', 'w') as file:
        json.dump(existing_data, file, indent=4)


class MeasureTakenTime:
    def __init__(self):
        self.now = None

    def measure(self):
        if self.now is None:
            self.now = time.time()
        else:
            elapsed_time = time.time() - self.now
            print("Elapsed time: {:.2f} seconds".format(elapsed_time))
            self.now = None


class Vehicle:
    id_counter = 0
    max_his_len = 5
    tolerance = 2.0

    def __init__(self, id, rect):
        self.id = id
        self.rect = rect
        self.parkedFrom = None  # is moving
        self.history = []

    def getCenterPoint(self):
        x, y, w, h = self.rect
        cx = (x + x + w) // 2
        cy = (y + y + h) // 2
        return (cx, cy)

    def updateHistory(self, rect):
        x, y, w, h = rect
        cx = (x + x + w) // 2
        cy = (y + y + h) // 2
        if len(self.history) >= Vehicle.max_his_len:
            self.history.pop(0)
        self.history.append((cx, cy))

    def update(self, rect):
        if self.rect != rect:
            self.parkedFrom = None
            self.updateHistory(rect)
        elif self.parkedFrom is None:
            self.parkedFrom = time.time()
        self.rect = rect

    def isParked(self):
        if self.parkedFrom is None:
            return False
        # over 2 seconds stay in mean: parked
        return time.time() - self.parkedFrom > 2

    def inDirection(self, point):
        return True
        if len(self.history) < Vehicle.max_his_len:
            return True
        x = [x[0] for x in self.history]
        slope, intercept, r, p, std_err = stats.linregress(x, y)
        try:
            expect_y = int(slope * point[0] + intercept)
            print(abs(expect_y - point[1]), end=' ')
            return abs(expect_y - point[1]) <= Vehicle.tolerance
        except:
            return True


class EuclideanDistTracker:
    threshold = 15.0

    def __init__(self):
        self.vehicles = {}
        self.id_count = Vehicle.id_counter

    def removeDuplicate(self):
        for key in list(self.vehicles.keys()):
            for other_key in self.vehicles.keys():
                if key != other_key and self.vehicles[key] == self.vehicles[other_key] and key > other_key:
                    print("del")
                    del self.vehicles[key]

    def getClosestId(self, cx, cy):
        closest_dist = float('inf')
        closest_id = None
        for id, ve in self.vehicles.items():
            pt = ve.getCenterPoint()
            dist = math.hypot(cx - pt[0], cy - pt[1])
            if dist < closest_dist and dist < EuclideanDistTracker.threshold and ve.inDirection((cx, cy)):
                closest_dist = dist
                closest_id = id
        same_object_detected = closest_dist < EuclideanDistTracker.threshold
        return same_object_detected, closest_id
    # def matchTemplate(self, rect):
    #     x, y, w, h = rect
    #     roi = frame[y:y+h, x:x+w]
    #     template = frame

    #     result = cv2.matchTemplate(template, roi, cv2.TM_CCOEFF_NORMED)

    #     # Find the location of the best match
    #     min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    #     top_left = max_loc
    #     bottom_right = (top_left[0] + w, top_left[1] + h)

    #     # Draw a rectangle around the matched area
    #     cv2.rectangle(template, top_left, bottom_right, (0, 0, 255), 2)

    #     cx = (x + x + w) // 2
    #     cy = (y + y + h) // 2
    #     return self.getClosestId(cx, cy)

    def updateOldTracker(self, objs):
        for id, ve in self.vehicles.items():
            closest_dist = float('inf')
            rect = ve.rect
            pt = ve.getCenterPoint()
            for obj in objs:
                x, y, w, h = obj
                cx = (x + x + w) // 2
                cy = (y + y + h) // 2
                dist = math.hypot(cx - pt[0], cy - pt[1])
                if dist < closest_dist and dist < EuclideanDistTracker.threshold and ve.inDirection((cx, cy)):
                    closest_dist = dist
                    rect = obj
            ve.update(rect)

        return [veh.rect + [veh.id] for idx, veh in self.vehicles.items()]

    # def checkParkedVehicle(self, specialFrames):
    #     for key in list(self.vehicles.keys()):
    #         if self.vehicles[key].isParked():
    #             for place in specialFrames:
    #                 if is_point_inside_rect(self.vehicles[key].getCenterPoint(), specialFrames[place]):
    #                     print("Vehicle {} is already parked at {} in {}".format(key, self.vehicles[key].getCenterPoint(), place))
    #             del self.vehicles[key]

    def checkParkedVehicle(self, ranges):
        # print("aaaaa")
        new_data = []
        for key in list(self.vehicles.keys()):
            if self.vehicles[key].isParked():
                for range_ in ranges:
                    if point_inside_polygon(self.vehicles[key].getCenterPoint(), range_["polygon"]):
                        new_data.append({
                            "key": f"{generate_random_vehicle_id()}",
                            "id": f"{key}",
                            "pos": f"{range_['id']}",
                            "coor": f"{self.vehicles[key].getCenterPoint()}",
                            "time": f"{datetime.now().strftime('%H:%M:%S')}"
                        })
                        print("Vehicle {} is already parked at {} in {}".format(
                            key, self.vehicles[key].getCenterPoint(), range_["id"]))
                del self.vehicles[key]
        if len(new_data) > 0:
            updateVehicleIdJsonData(new_data)

    def addNewTracker(self, objects_rect):
        for rect in objects_rect:
            x, y, w, h = rect
            cx = (x + x + w) // 2
            cy = (y + y + h) // 2

            same_object_detected, id = self.getClosestId(cx, cy)
            if same_object_detected:
                continue
            else:  # New object is detected we assign the ID to that object
                self.vehicles[self.id_count] = Vehicle(self.id_count, rect)
                self.id_count += 1


trackerED = EuclideanDistTracker()


class AppTracking:
    vehicleArea = 30.0
    emptyArea = 100.0

    def __init__(self, path="server/public/videos/longest.mp4"):
        self.cap = cv2.VideoCapture(path)
        self.object_detector = cv2.createBackgroundSubtractorMOG2(
            history=200, varThreshold=50, detectShadows=False)
        self.ret, self.frame = self.cap.read()
        self.mTT = MeasureTakenTime()
        self.specialFrame = {
            "gate": [600, 70, self.frame.shape[1] - 600 - 80, 70]
        }

        self.isSettingRanges = False
        self.ranges = []

        self.firstFrame = None

        self.collectFirstFrame()
        self.loadMultiRanges()

        self.call_function_with_interval_2()

    def getPolygonFrame(self, frame, polygon):
        mask = np.zeros_like(frame[:, :, 0])
        cv2.fillPoly(mask, [np.array(polygon)], 255)
        sub_frame = cv2.bitwise_and(frame, frame, mask=mask)
        return sub_frame

    def showAreaOfEmptyInRanges(self, contours):
        list_area = []
        for contour in contours:
            area = cv2.contourArea(contour)
            list_area.append(area)
            list_area.sort(reverse=True)
        return list_area
    
    def notifyVehicleCoordination(self, centerPoint, timeLeft):
        if datetime.now() - timeLeft >= timedelta(seconds = 5):
            threading.Timer(0, threading._shutdown).start()
            return        
        threading.Timer(0.1, self.notifyVehicleCoordination, args=(centerPoint, timeLeft)).start()
        cv2.circle(self.frame, centerPoint, 1, (0, 0, 255), 2)
        cv2.circle(self.frame, centerPoint, 10, (0, 0, 255), 2)
        cv2.circle(self.frame, centerPoint, 15, (0, 0, 255), 2)
        # cv2.imshow("finding", self.frame)
        # cv2.waitKey(0)
    
    def findVehicleId(self, key):
        with open('server\database\\vehicle_id.json', 'r') as file:
            existing_data = json.load(file)
        for vehicle in existing_data:
            if vehicle["key"] == key:
                print("finding vehicle with id", key)
                point = tuple(map(int, vehicle["coor"].strip("()").split(",")))
                point = np.array(point)
                self.notifyVehicleCoordination(point, timeLeft=datetime.now())

    def call_function_with_interval_2(self):
        self.trackEmptyInRanges(self.frame)
        threading.Timer(2.0, self.call_function_with_interval_2).start()

    def trackEmptyInRanges(self, frame):
        # if datetime.now() - self.lastCallTime["trackEmptyInRanges"] < timedelta(seconds=2): return
        # self.lastCallTime["trackEmptyInRanges"]  = datetime.now()
        # print("start at", datetime.now())
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

            empty_areas = self.showAreaOfEmptyInRanges(contours)
            # print(empty_areas)
            if empty_areas[0] >= AppTracking.emptyArea:
                # print(f"{range_['id']} has empty place can park")
                self.ranges[idx]["empty"] = True
            else:
                self.ranges[idx]["empty"] = False

            # cv2.imshow(f"empty places", contour_image)
            # cv2.waitKey(10)
        # print("end at", datetime.now())

    def getAllRanges(self):
        return self.ranges

    def getResultFrame(self):
        return self.frame

    def collectFirstFrame(self):
        self.ret, self.frame = self.cap.read()
        while not self.ret:
            self.ret, self.frame = self.cap.read()
        self.firstFrame = self.frame

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if not self.isSettingRanges:
                self.ranges.append({
                    "polygon": [],
                    "id": f"range {len(self.ranges)}",
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
                # for range_ in self.ranges:
                #     for point in range_["polygon"]:
                #         x, y = point
                #         cv2.circle(self.firstFrame, (x, y), 1, (0, 255, 0), 5)

                cv2.imshow('Set multi ranges', self.firstFrame)

                # Wait for a key press
                key = cv2.waitKey(1) & 0xFF

                # Exit the loop if 'esc' is pressed
                if key == 27:
                    break
            output_file = 'server\database\\ranges.json'
            with open(output_file, 'w') as f:
                json.dump(self.ranges, f)

    def loadMultiRanges(self):
        with open('server\database\\ranges.json', 'r') as f:
            self.ranges = json.load(f)

    def run(self):
        # self.setSpecialFrame(cv2.selectROI(self.frame), "gate")
        # self.setSpecialFrame(cv2.selectROI(self.frame), "range A")
        # self.setSpecialFrame(cv2.selectROI(self.frame), "range B")

        # self.setMultiRanges()
        self.loadMultiRanges()

        while True:
            self.ret, self.frame = self.cap.read()
            if not self.ret:
                continue
            roi = self.frame
            detected_rect = self.detect(roi)

            specFrame = self.getSpecialFrame()
            detected_rect_roi = [
                rect for rect in detected_rect if is_rect_inside_another(rect, specFrame)]

            trackerED.addNewTracker(detected_rect_roi)
            boxes_ids = trackerED.updateOldTracker(detected_rect)
            trackerED.checkParkedVehicle(self.ranges)
            trackerED.removeDuplicate()

            self.drawPolygonSettings()

            for box_id in boxes_ids:
                x, y, w, h, id = box_id
                cv2.putText(roi, str(id), (x, y - 10),
                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)
                cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 1)

            roi = self.getRoi(self.frame, self.getSpecialFrame())

            # cv2.imshow("Mask", self.mask)
            cv2.imshow("Ranges", self.firstFrame)
            cv2.imshow("Frame", self.frame)
            # cv2.imshow("Roi", roi)

            key = cv2.waitKey(10)
            if key == 27:
                break

        self.cap.release()
        cv2.destroyAllWindows()

    def work(self):
        self.ret, self.frame = self.cap.read()
        roi = self.frame
        detected_rect = self.detect(roi)

        specFrame = self.getSpecialFrame()
        detected_rect_roi = [
            rect for rect in detected_rect if is_rect_inside_another(rect, specFrame)]

        trackerED.addNewTracker(detected_rect_roi)
        boxes_ids = trackerED.updateOldTracker(detected_rect)
        # trackerED.checkParkedVehicle(self.getAllSpecialFrames())
        trackerED.checkParkedVehicle(self.ranges)
        trackerED.removeDuplicate()

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
            if area > AppTracking.vehicleArea:
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

# AppTracking().run()
