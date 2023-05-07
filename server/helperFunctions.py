import random
import json
import numpy as np
import string
import cv2
import time

def read_json_file(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

def write_json_file(filename, new_data):
    with open(filename, 'w') as file:
        json.dump(new_data, file, indent=4)

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
    file_path = 'server\database\\vehicles.json'
    existing_data = read_json_file(file_path)
    existing_data += new_data
    write_json_file(file_path, existing_data)

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

class SimulateData:
    def __init__(self):
        pass
    def random_temp_data(self):
        return "{:.2f}".format(random.uniform(20.0, 30.0))
    def random_humi_data(self):
        return str(int(random.uniform(40.0, 60.0)))