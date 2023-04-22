import cv2
from vehicle import *


class Detector:
    def __init__(self, frame):
        self.frame = frame
        self.object_detector = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=50, detectShadows=False)
        self.vehicles = []
    def getSpecialFrame(self):
        # x, y, w, h
        rect = [600, 50, self.frame.shape[1] - 600, 130]
        return rect
    def update(self, frame):
        self.frame = frame
    def getRoi(self):
        rect = self.getSpecialFrame()
        x, y, w, h = rect
        return self.frame[y:y+h,x:x+w]
    def getRoiInFrame(self, boxes):
        rect = self.getSpecialFrame()
        for box in boxes:
            box[0] += rect[0]
            box[1] += rect[1]
        return boxes
    def paddingRect(self, rect, pad):
        x, y, w, h = rect
        x, y, w, h = x - pad, y - pad, w + pad * 2, h + pad * 2
        return [x, y, w, h]

    def updateDetections(self, detections):
        for vehicle in self.vehicles:
            template = vehicle.frame
            template_width, template_height = template.shape[1], template.shape[0]

            x,y,w,h = self.paddingRect(vehicle.rect, 20)
            frame = self.frame[y:y+h,x:x+w]
            rect = self.getRoiInFrame([x,y,w,h])
            result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            top_left = max_loc
            bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
            cv2.rectangle(self.frame, top_left, bottom_right, (255, 0, 255), 2)

    def run(self):
        roi = self.getRoi()
        detections = self.detect(roi)
        detections = self.getRoiInFrame(detections)
        
        self.updateDetections(detections)
        self.drawRectDetectedVehicles(detections)

        self.vehicles = [Vehicle(rect, self.frame[y:y+h, x:x+w]) for rect in detections for x, y, w, h in [rect]]
    def detect(self, roi):
        mask = self.object_detector.apply(roi)
        detections = []

        # remove faded
        _, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            if area > 30.0:
                # print(x, y, w, h)
                detections.append([x, y, w, h])
        return detections
    def getVehicles(self):
        return self.vehicles
    def drawRectDetectedVehicles(self, boxes):
        for box in boxes:
            x, y, w, h = box
            cv2.rectangle(self.frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
        cv2.imshow("detectVehicle", self.frame)
        cv2.imshow("roi", self.getRoi())