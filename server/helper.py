import cv2
import numpy as np

# define global variables
drawing = False
finished = False
vertices = []

# define mouse callback function
def draw_roi(event, x, y, flags, param):
    global drawing, finished, vertices
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        vertices.append((x, y))
    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            img_temp = img.copy()
            cv2.line(img_temp, vertices[-1], (x, y), (255, 0, 0), 2)
            cv2.imshow('image', img_temp)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        vertices.append((x, y))
        img_temp = img.copy()
        cv2.line(img_temp, vertices[-2], vertices[-1], (255, 0, 0), 2)
        cv2.imshow('image', img_temp)
    elif event == cv2.EVENT_RBUTTONDOWN:
        finished = True

# read an image from file
img = cv2.imread('server/public/videos/syntaxLS.png')

# create a window and set mouse callback function
cv2.namedWindow('image')
cv2.setMouseCallback('image', draw_roi)

# loop until ROI is selected
while not finished:
    cv2.imshow('image', img)
    cv2.waitKey(1)

# create a mask from the polygonal ROI
mask = np.zeros(img.shape[:2], dtype=np.uint8)
roi_corners = np.array(vertices, dtype=np.int32)
cv2.fillPoly(mask, [roi_corners], 255)

# apply the mask to the original image
masked_img = cv2.bitwise_and(img, img, mask=mask)

# display the masked image in a new window
cv2.imshow('ROI', masked_img)
cv2.waitKey(0)
cv2.destroyAllWindows()
