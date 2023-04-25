import cv2
from tracker import *
import math
import time
import numpy as np
from scipy import stats, polyfit
# from polyROISelector import polyROISelector
from sklearn.linear_model import LinearRegression

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
        self.parkedFrom = None # is moving
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
        elif self.parkedFrom is None: self.parkedFrom = time.time()
        self.rect = rect
    def isParked(self):
        if self.parkedFrom is None: return False
        # over 2 seconds stay in mean: parked
        return time.time() - self.parkedFrom > 2
    def inDirection(self, point):
        return True
        if len(self.history) < Vehicle.max_his_len: return True
        x = [x[0] for x in self.history]
        slope, intercept, r, p, std_err = stats.linregress(x, y)
        try:
            expect_y = int(slope * point[0] + intercept)
            print( abs(expect_y - point[1]), end = ' ')
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
                x,y,w,h = obj
                cx = (x + x + w) // 2
                cy = (y + y + h) // 2
                dist = math.hypot(cx - pt[0], cy - pt[1])
                if dist < closest_dist and dist < EuclideanDistTracker.threshold and ve.inDirection((cx, cy)):
                    closest_dist = dist
                    rect = obj                    
            ve.update(rect)

        return [veh.rect + [veh.id] for idx, veh in self.vehicles.items()]
    
    def checkParkedVehicle(self, specialFrames):
        for key in list(self.vehicles.keys()):
            if self.vehicles[key].isParked():
                for place in specialFrames:
                    if is_point_inside_rect(self.vehicles[key].getCenterPoint(), specialFrames[place]):
                        print("Vehicle {} is already parked at {} in {}".format(key, self.vehicles[key].getCenterPoint(), place))
                del self.vehicles[key]

    def addNewTracker(self, objects_rect):
        for rect in objects_rect:
            x, y, w, h = rect
            cx = (x + x + w) // 2
            cy = (y + y + h) // 2

            same_object_detected, id = self.getClosestId(cx, cy)
            if same_object_detected:
                continue
            else: # New object is detected we assign the ID to that object
                self.vehicles[self.id_count] = Vehicle(self.id_count, rect)
                self.id_count += 1



trackerED = EuclideanDistTracker()

class App:
    data_path = "server/public/videos/longest.mp4"
    vehicleArea = 30.0
    def __init__(self):
        self.cap = cv2.VideoCapture(App.data_path)
        self.object_detector = cv2.createBackgroundSubtractorMOG2(
            history=200, varThreshold=50, detectShadows=False)
        self.ret, self.frame = self.cap.read()
        self.mTT = MeasureTakenTime()
        self.specialFrame = {
            "gate": [600, 70, self.frame.shape[1] - 600 - 80, 70]
        }
    def run(self):
        self.setSpecialFrame(cv2.selectROI(self.frame), "gate")
        # self.setSpecialFrame(cv2.selectROI(self.frame), "range A")
        # self.setSpecialFrame(cv2.selectROI(self.frame), "range B")
        while True:
            self.ret, self.frame = self.cap.read()
            if not self.ret: continue
            roi = self.frame
            detected_rect = self.detect(roi)

            specFrame = self.getSpecialFrame()
            detected_rect_roi = [rect for rect in detected_rect if is_rect_inside_another(rect, specFrame)]

            trackerED.addNewTracker(detected_rect_roi)
            boxes_ids = trackerED.updateOldTracker(detected_rect)
            trackerED.checkParkedVehicle(self.getAllSpecialFrames())
            trackerED.removeDuplicate()

            for box_id in boxes_ids:
                x, y, w, h, id = box_id
                cv2.putText(roi, str(id), (x, y - 10),
                            cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)
                cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 1)

            roi = self.getRoi(self.frame, self.getSpecialFrame())
            cv2.imshow("Mask", self.mask)
            cv2.imshow("Frame", self.frame)
            cv2.imshow("Roi", roi)

            key = cv2.waitKey(10)
            if key == 27:
                break

        self.cap.release()
        cv2.destroyAllWindows()
    def detect(self, roi) -> list():
        mask = self.object_detector.apply(roi)
        detections = []

        _, self.mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            if area > App.vehicleArea:
                detections.append([x, y, w, h])
        return detections
    def setSpecialFrame(self, rect, name = "gate"):
        self.specialFrame[name] = rect
    def getSpecialFrame(self, name = "gate"):
        return self.specialFrame[name]
    def getAllSpecialFrames(self):
        return self.specialFrame
    def getRoi(self, frame, rect):
        x, y, w, h = rect
        return frame[y:y+h,x:x+w]
App().run()