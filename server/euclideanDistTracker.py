from helperFunctions import *
from vehicle import Vehicle
import math
from datetime import datetime

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
