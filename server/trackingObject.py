import cv2
import time
import numpy as np

data_path = "public/videos/video.mp4"

def get_center_point(rect):
    x, y, w, h = rect
    cx = (x + x + w) // 2
    cy = (y + y + h) // 2
    return [cx, cy]

class Tracker:
    def __init__(self, frame, box):
        self.tracker = cv2.legacy.TrackerCSRT_create()
        self.tracker.init(frame, box)
        self.history = {}
        self.history['center_points'] = []
    def getCenterPoints(self):
        return self.history['center_points']
    def isStopping(self):
        cnt = np.array(self.history['center_points'], dtype=np.int32)
        if len(cnt) > 50:
            # x, y, w, h = cv2.boundingRect(cnt)
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            distance1 = cv2.norm(box[0], box[1], cv2.NORM_L2)
            distance2 = cv2.norm(box[1], box[2], cv2.NORM_L2)
            width = max(distance1, distance2)
            print(width)
            if width < 8:
                return True
            self.history['center_points'] = []
        return False
    def update(self, frame):
        _, box = self.tracker.update(frame)
        self.history['center_points'].append(get_center_point(box))
        return _, box
class App:
    def __init__(self, path: str):
        self.cap = cv2.VideoCapture(path)
        self.ret, self.frame = self.cap.read()
        # print(self.frame.shape) #height, width
        # self.trackers = cv2.legacy.MultiTracker_create()
        self.trackers = []
        self.boxes = []
    def addTracker(self, frame, box):
        tracker = Tracker(frame, box)
        self.trackers.append(tracker)
    def getROI(self, frame):
        for i in range(0, 1):
            bbox = cv2.selectROI('Select Object', frame, False)

            bbox = self.traceBox(self.rect, bbox)
            cv2.rectangle(self.frame, (bbox[0], bbox[1]), (bbox[0]+bbox[2], bbox[1]+bbox[3]), (255, 0, 0), 2)
            self.boxes.append(bbox)
            self.addTracker(self.frame, bbox)
    def detectObject(self, frame):
        self.getROI(frame)
        # self.trackers.add(tracker, self.frame, bbox)

    def drawBoundingTracker(self):
        for box in self.boxes:
            x, y, w, h = [int(i) for i in box]
            cv2.rectangle(self.frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    def updateTracers(self):
        # success, self.boxes = self.trackers.update(self.frame)
        self.boxes = []
        for tracker in self.trackers:
            _, box = tracker.update(self.frame)
            if _:
                self.boxes.append(box)
        
        self.trackers = [tracker for tracker in self.trackers if tracker.isStopping() is False]
    def drawCenterPointsTracer(self):
        for tracker in self.trackers:
            centerPoints = tracker.getCenterPoints()
            for p in centerPoints:
                # print(p, end=' ')
                cv2.circle(self.frame, (int(p[0]), int(p[1])), 2, (255,255,255), -1)
    def dropFrame(self, frame, rect):
        # return frame[0: 50, 650: self.frame.shape[1]]
        return frame[rect[1]: rect[1] + rect[3], rect[0]: rect[0] + rect[2]]
    def traceBox(self, rect, box):
        return (box[0] + rect[0], box[1] + rect[1], box[2], box[3]) #hold w, h
    def run(self):
        self.rect = [600, 0, self.frame.shape[1] - 600, 100] # x, y, w, h
        while True:
            self.ret, self.frame = self.cap.read()

            drop = self.dropFrame(self.frame, self.rect)
            if cv2.waitKey(1) & 0xFF == ord('a'):
                self.detectObject(drop)

            self.updateTracers()
            
            self.drawCenterPointsTracer()

            self.drawBoundingTracker()

            cv2.imshow('Object Tracking', self.frame)
            cv2.imshow('Drop', drop)

            if self.handleBreak():
                break
        self.cap.release()
        cv2.destroyAllWindows()

    def handleBreak(self):
        if cv2.waitKey(1) & 0xFF == ord('q'):
            return True
        return False

    def trace(self):
        self.object_detector = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=10)
        dots = []
        self.gray = np.zeros([self.frame.shape[0],self.frame.shape[1],1],dtype=np.uint8)
        current = time.time()
        self.boxes = []
        while True:
            if time.time() - current > 5:                            
                current = time.time()
                dots = []
            _, self.frame = self.cap.read()
            mask = self.object_detector.apply(self.frame)
            _, mask = cv2.threshold(mask , 254, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            objects_position = []
            for cnt in contours:
                # remove small area
                area = cv2.contourArea(cnt)
                if area > 100:
                    x, y, w, h = cv2.boundingRect(cnt)
                    objects_position.append([x, y, w, h])
                    cx = (x + x + w) // 2
                    cy = (y + y + h) // 2
                    dots.append((cx, cy))
            self.gray = np.zeros([self.frame.shape[0],self.frame.shape[1],1],dtype=np.uint8)
            for dot in dots:
                cv2.circle(self.gray, dot, 5, (255,255,255), -1)
            contours, _ = cv2.findContours(self.gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            # print(contours)
            for cnt in contours:
                # print(type(cnt))
                area = cv2.contourArea(cnt) # for circle moving
                if area > 500:
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(self.frame, (x, y), (x + w, y + h), (0, 255, 0))
                    # print(x, y, w, h)
                    if max(w, h) / min(h, w) > 3.0:
                        self.boxes.append([x, y, w, h])
            for box in self.boxes:
                [x, y, w, h] = box
                # print(x, y, w, h)
                cv2.rectangle(self.frame, (x, y), (x + w, y + h), (0, 255, 0))
            cv2.imshow('Object Selection', self.frame)
            cv2.imshow('Object Center', self.gray)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

App(data_path).trace()
