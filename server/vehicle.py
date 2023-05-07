import time

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