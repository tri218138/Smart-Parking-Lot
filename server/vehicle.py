class Vehicle:
    def __init__(self, rect, frame, id = -1):
        self.id = id
        self.rect = rect
        self.frame = frame
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
        return self.parking > 5