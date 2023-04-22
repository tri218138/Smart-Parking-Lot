import cv2
from tracker import *
import math
import time
import numpy as np


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

mTT = MeasureTakenTime()

data_path = "server/public/videos/longest.mp4"
cap = cv2.VideoCapture(data_path)

object_detector = cv2.createBackgroundSubtractorMOG2(
    history=200, varThreshold=50, detectShadows=False)

ret, frame = cap.read()

# class Vehicle:
#     def __init__(self, id, rect):
#         self.id = id
#         self.rect = rect
#     def getCenterPoint(self):
#         x, y, w, h = self.rect
#         cx = (x + x + w) // 2
#         cy = (y + y + h) // 2
#         return (cx, cy)
#     def update(self, rect):
            # self.rect = rect
class Vehicle:
    def __init__(self, id, rect):
        self.id = id
        self.rect = rect
        # self.frame = frame
        self.parking = 0
    def getCenterPoint(self):
        x, y, w, h = self.rect
        cx = (x + x + w) // 2
        cy = (y + y + h) // 2
        return (cx, cy)
    def update(self, rect):
        if self.rect == rect:
            self.parking += 1
        else:
            self.parking = 0
        self.rect = rect
    def isParked(self):
        return self.parking > 10


class EuclideanDistTracker:
    def __init__(self):
        # Store the center positions of the objects
        # self.center_points = {}
        self.vehicles = {}
        # Keep the count of the IDs
        # each time a new object id detected, the count will increase by one
        self.id_count = 0
    def removeDuplicate(self):
        for key in list(self.vehicles.keys()):
            for other_key in self.vehicles.keys():
                if key != other_key and self.vehicles[key] == self.vehicles[other_key] and key > other_key:
                    print("del")
                    del self.vehicles[key]

    def getClosestId(self, cx, cy):
        closest_dist = float('inf')
        closest_id = None

        # iterate over center points
        for id, ve in self.vehicles.items():
                # calculate Euclidean distance
            pt = ve.getCenterPoint()
            dist = math.hypot(cx - pt[0], cy - pt[1])
            # update closest distance and ID if this point is closer
            # print(dist)
            if dist < closest_dist and dist < 25:
                closest_dist = dist
                closest_id = id
        same_object_detected = False
        if closest_dist < 25.0:
            same_object_detected = True
        return same_object_detected, closest_id
    def matchTemplate(self, rect):
        x, y, w, h = rect
        roi = frame[y:y+h, x:x+w]
        template = frame

        result = cv2.matchTemplate(template, roi, cv2.TM_CCOEFF_NORMED)
        

        # Find the location of the best match
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)

        # Draw a rectangle around the matched area
        cv2.rectangle(template, top_left, bottom_right, (0, 0, 255), 2)

        cx = (x + x + w) // 2
        cy = (y + y + h) // 2
        return self.getClosestId(cx, cy)    

    def isSameObjectDetected(self):
        pass

    def update2(self, objs):
        for id, ve in self.vehicles.items():
            closest_dist = float('inf')
            rect = ve.rect
            pt = ve.getCenterPoint()
            for obj in objs:
                x,y,w,h = obj
                cx = (x + x + w) // 2
                cy = (y + y + h) // 2
                dist = math.hypot(cx - pt[0], cy - pt[1])
                # update closest distance and ID if this point is closer
                # print(dist)
                if dist < closest_dist and dist < 25:
                    closest_dist = dist
                    rect = obj                    
            ve.update(rect)
        for key in list(self.vehicles.keys()):
            if self.vehicles[key].isParked():
                print("Vehicle {} is already parked".format(key))
                del self.vehicles[key]
        return [veh.rect + [veh.id] for idx, veh in self.vehicles.items()]

    def update(self, objects_rect):
        # Objects boxes and ids
        objects_bbs_ids = []

        # Get center point of new object
        
        for rect in objects_rect:
            x, y, w, h = rect
            cx = (x + x + w) // 2
            cy = (y + y + h) // 2

            # Find out if that object was detected already
            same_object_detected, id = self.getClosestId(cx, cy)
            # same_object_detected, id = self.matchTemplate(rect)
            if same_object_detected:
                continue
                self.vehicles[id].update(rect)
                # print(self.center_points[id])
                objects_bbs_ids.append([x, y, w, h, id])
            else: # New object is detected we assign the ID to that object
                self.vehicles[self.id_count] = Vehicle(self.id_count, rect)
                objects_bbs_ids.append([x, y, w, h, self.id_count])
                self.id_count += 1

        # Clean the dictionary by center points to remove IDS not used anymore
        # new_vehicles = {}
        # for obj_bb_id in objects_bbs_ids:
        #     _, _, _, _, object_id = obj_bb_id
        #     # center = self.vehicles[object_id].getCenterPoint()
        #     new_vehicles[object_id] = self.vehicles[object_id]

        # Update dictionary with IDs not used removed
        # self.vehicles = new_vehicles.copy()
        return objects_bbs_ids



trackerED = EuclideanDistTracker()

def detect(roi):
    mask = object_detector.apply(roi)
    detections = []

    # remove faded
    _, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # mask = cv2.adaptiveThreshold(mask, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10)
    contours, _ = cv2.findContours(
        mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    cntObjectContour = 0
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = cv2.contourArea(cnt)
        if area > 30.0:
            cntObjectContour += 1
            # cv2.drawContours(roi, [cnt], -1, (0, 255, 0), 2)
            detections.append([x, y, w, h])
    return detections
def is_rect_inside_another(rect1, rect2):
    if rect1[0] >= rect2[0] and rect1[1] >= rect2[1] and rect1[0] + rect1[2] <= rect2[0] + rect2[2] and rect1[1] + rect1[3] <= rect2[1] + rect2[3]:
        return True
    else:
        return False
def getSpecialFrame(frame):
    # x, y, w, h
    rect = [600, 70, frame.shape[1] - 600 - 80, 70]
    return rect
def getRoi(frame):
    rect = getSpecialFrame(frame)
    x, y, w, h = rect
    return frame[y:y+h,x:x+w]
now = time.time()
while True:
    ret, frame = cap.read()
    if not ret: continue
    roi = frame
    detections = detect(roi)

    specFrame = getSpecialFrame(frame)
    subDetections = [rect for rect in detections if is_rect_inside_another(rect, specFrame)]
    boxes_ids = trackerED.update(subDetections)
    boxes_ids = trackerED.update2(detections)
    trackerED.removeDuplicate()
    # print(trackerED.vehicles)

    for box_id in boxes_ids:
        x, y, w, h, id = box_id
        cv2.putText(roi, str(id), (x, y - 10),
                    cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 0), 1)
        cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 1)

        
    roi = getRoi(frame)
    # cv2.imshow("Mask", mask)
    cv2.imshow("Frame", frame)
    cv2.imshow("Roi", roi)

    key = cv2.waitKey(10)
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()
